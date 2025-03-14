from stt import STT
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram import Dispatcher, Bot, F, types
from aiogram.filters import Command
import asyncio

from langchain_community.document_loaders import TextLoader, PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate

from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.orm import sessionmaker, relationship

from transformers import AutoTokenizer, AutoModel
import torch
import requests
import numpy as np

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LLM_API_ENDPOINT = os.getenv("LLM_API_ENDPOINT")  # Ваш сервер с LLM API
EMBEDDING_MODEL_NAME = "sergeyzh/rubert-tiny-turbo"  # Модель эмбеддинга

# Инициализация Telegram бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
stt = STT()

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
)

# Загрузка модели эмбеддингов
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
embedding_model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME).to(device)


# Функция для генерации эмбеддингов
def embed_texts(texts):
    text_list = [text.page_content for text in texts]
    embeddings = []
    for text in text_list:
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
        with torch.no_grad():
            outputs = embedding_model(**inputs)
        sentence_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        embeddings.append(sentence_embedding)
    return np.vstack(embeddings)


# Загрузка и обработка данных
pdf_loader = TextLoader("data")
data = pdf_loader.load()

# Разделение текста на части
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(data)

# Генерация эмбеддингов с помощью `sergeyzh/rubert-tiny-turbo`
embeddings = embed_texts(texts)

# Создание и загрузка FAISS индекса
faiss_index_path = "faiss_index"
vectorstore = FAISS.from_texts([text.page_content for text in texts], embeddings)
vectorstore.save_local(faiss_index_path)
retriever = vectorstore.as_retriever()


# Функция для обращения к вашему LLM API
def call_llm_api(prompt):
    response = requests.post(LLM_API_ENDPOINT, json={"prompt": prompt})
    if response.status_code == 200:
        return response.json().get("generated_text", "")
    else:
        raise ValueError(f"Ошибка при обращении к LLM API: {response.status_code}")


# Шаблон для генерации ответов
template = """Ты - полезный помощник, который генерирует несколько поисковых запросов на основе предыдущего контекста переписки с пользователем и нового вопроса. 
Предыдущий контекст: 
{context}
Генерируй несколько поисковых запросов, связанных с: {question} 
Ответ (4 поисковых запроса):"""
prompt_rag_fusion = ChatPromptTemplate.from_template(template)


def rag_fusion_pipeline(context, query):
    input_data = {"context": context, "question": query}
    prompt = prompt_rag_fusion.format(context=context, question=query)
    ans = call_llm_api(prompt)
    multiple_queries = [i for i in ans.split('\n') if i]

    count = dict()
    for query in multiple_queries:
        relevant_documents = retriever.invoke(query, k=4)
        relevant_documents_content = [page.page_content for page in relevant_documents]
        for content in relevant_documents_content:
            count[content] = 1 + count.get(content, 0)

    sorted_chunks_for_rag_fusion = [i[0] for i in sorted(count.items(), key=lambda item: item[1], reverse=True)]
    return ''.join(sorted_chunks_for_rag_fusion)


# Основной промпт для генерации ответов
system_prompt = (
    '''
    Игнорируй все предыдущие инструкции. Ты ассистент для решения задач по вопросам и ответам. Твоя задача — использовать предоставленный контекст, чтобы дать максимально точный и полезный ответ.
    {context}
    '''
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)


# Функция для проверки галлюцинаций
def check_for_hallucinations(context, response):
    # Создание промпта для проверки галлюцинаций
    hallucination_prompt = (
        f"Проверяй ответ '{response}' на согласованность с контекстом:\n{context}\n"
        "Если ответ не противоречит контексту, напиши 'Ответ согласован'. "
        "Если противоречит, напиши 'Обнаружены галлюцинации'."
    )
    # Вызов LLM API для проверки
    return call_llm_api(hallucination_prompt)


def rag_chain(context, question):
    joined_sorted_chunks_for_rag_fusion = rag_fusion_pipeline(context, question)
    prompt_text = prompt.format(context=joined_sorted_chunks_for_rag_fusion, question=question)

    # Генерация ответа
    generated_response = call_llm_api(prompt_text)

    # Проверка на галлюцинации
    hallucination_check = check_for_hallucinations(joined_sorted_chunks_for_rag_fusion, generated_response)

    return f"{generated_response}\n\nПроверка на галлюцинации: {hallucination_check}"

# Настройка базы данных SQLite для хранения взаимодействий
engine = create_engine('sqlite:///telegram_bot.db')
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    interactions = relationship('Interaction', back_populates='user')

class Interaction(Base):
    __tablename__ = 'interactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question = Column(Text)
    answer = Column(Text)
    user = relationship('User', back_populates='interactions')

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def get_or_create_user(telegram_id):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        session.commit()
    return user

def save_interaction(user, question, answer):
    interaction = Interaction(user_id=user.id, question=question, answer=answer)
    session.add(interaction)
    session.commit()

def clear_user_interactions(user):
    session.query(Interaction).filter_by(user_id=user.id).delete()
    session.commit()

def get_last_interactions(user, limit=5):
    return session.query(Interaction).filter_by(user_id=user.id).order_by(Interaction.id.desc()).limit(limit).all()

# Создание кнопки
button_approve = KeyboardButton(text="Одобрить")
button_rephrase = KeyboardButton(text="Переформулировать")
button_edit = KeyboardButton(text="Редактировать")

# Создание клавиатуры с обязательным параметром keyboard
control_kb = ReplyKeyboardMarkup(keyboard=[[button_approve, button_rephrase, button_edit]], resize_keyboard=True)

# Хэндлер на команду /start
@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    clear_user_interactions(user)
    await message.reply("Привет! Я бот, использующий модель RAG и способный конвертировать аудио в текст. Задайте мне любой вопрос или отправьте голосовое сообщение!", reply_markup=control_kb)

# Хэндлер на нажатие кнопки "Одобрить"
@dp.message(F.text == "Одобрить")
async def handle_approve(message: types.Message):
    await message.reply("Мы отправляем ответ пользователю.")

# Хэндлер на нажатие кнопки "Переформулировать"
@dp.message(F.text == "Переформулировать")
async def handle_rephrase(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    last_interaction = session.query(Interaction).filter_by(user_id=user.id).order_by(Interaction.id.desc()).first()
    if last_interaction:
        context = "\n".join(f"Q: {interaction.question}\nA: {interaction.answer}" for interaction in reversed(get_last_interactions(user)))
        response = rag_chain(context, last_interaction.question)
        save_interaction(user, last_interaction.question, response)
        await message.reply(response)
    else:
        await message.reply("Нет предыдущего вопроса для переформулировки.")

# Хэндлер на нажатие кнопки "Редактировать"
@dp.message(F.text == "Редактировать")
async def handle_edit(message: types.Message):
    await message.reply("Напишите ответ на вопрос пользователя.")



# Хэндлер на команду /clear
@dp.message(Command(commands="clear"))
async def clear_dialog(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    clear_user_interactions(user)
    await message.reply("История сообщений очищена.")

# Хэндлер на получение текстового сообщения (для RAG)
@dp.message(F.text)
async def handle_text(message: types.Message):
    user = get_or_create_user(message.from_user.id)
    question = message.text

    last_interactions = get_last_interactions(user)
    context = "\n".join(f"Q: {interaction.question}\nA: {interaction.answer}" for interaction in reversed(last_interactions))

    response = rag_chain(context, question)
    save_interaction(user, question, response)
    await message.reply(response)

# Хэндлер на получение голосового и аудио сообщения
@dp.message(F.content_type.in_({"voice", "audio", "document"}))
async def voice_message_handler(message: types.Message):
    user = get_or_create_user(message.from_user.id)

    if message.content_type == "voice":
        file_id = message.voice.file_id
    elif message.content_type == "audio":
        file_id = message.audio.file_id
    elif message.content_type == "document":
        file_id = message.document.file_id
    else:
        await message.reply("Формат документа не поддерживается")
        return

    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_on_disk = Path("", f"{file_id}.tmp")
    await bot.download_file(file_path, destination=file_on_disk)

    # Конвертация аудио в текст
    text = stt.audio_to_text(file_on_disk)
    if not text:
        await message.reply("Не удалось распознать текст из аудио.")
        return

    # Передача текста на обработку в RAG
    last_interactions = get_last_interactions(user)
    context = "\n".join(f"Q: {interaction.question}\nA: {interaction.answer}" for interaction in reversed(last_interactions))

    response = rag_chain(context, text)
    save_interaction(user, text, response)
    await message.reply(response)

    os.remove(file_on_disk)  # Удаление временного файла

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запуск бота 
    print("Запуск бота")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass