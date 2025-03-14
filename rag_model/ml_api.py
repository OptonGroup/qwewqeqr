import requests
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from transformers import AutoTokenizer, AutoModel
import torch
import os
import numpy as np
from dotenv import load_dotenv
import uvicorn

# Загрузка переменных окружения
load_dotenv()


LLM_API_ENDPOINT = os.getenv("LLM_API_ENDPOINT")
if not LLM_API_ENDPOINT:
    LLM_API_ENDPOINT = "http://localhost:5000/generate"  # значение по умолчанию 

# Параметры для использования эмбеддинга `sergeyzh/rubert-tiny-turbo`
model_name = "sergeyzh/rubert-tiny-turbo"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Инициализация модели эмбеддингов
tokenizer = AutoTokenizer.from_pretrained(model_name)
embedding_model = AutoModel.from_pretrained(model_name).to(device)

# Классы данных для запросов и ответов
class Request(BaseModel):
    question: str


class Response(BaseModel):
    answer: str
    class_1: str
    class_2: str


# Инициализация FastAPI
app = FastAPI()

@app.get("/")
def index():
    return {"text": "Интеллектуальный помощник."}

# Шаг 1: Функция для получения эмбеддингов с использованием `sergeyzh/rubert-tiny-turbo`
def embed_texts(texts):
    text_list = [text.page_content for text in texts]
    embeddings = []
    for text in text_list:
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
        with torch.no_grad():
            outputs = embedding_model(**inputs)
        # Усреднение эмбеддингов по всем токенам (или возьмите [CLS] токен)
        sentence_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        embeddings.append(sentence_embedding)
    # Преобразуем вектора в формат NumPy
    return np.vstack(embeddings)

print('Начало загрузки данных')

# Шаг 2: Загрузка данных из PDF или текстовых файлов
data_dir = r"data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    print(f"Создана директория для данных: {data_dir}")

try:
    pdf_loader = PyPDFDirectoryLoader(data_dir)
    data = pdf_loader.load()
    
    # Шаг 3: Разделение текста на части
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(data)
    
    # Шаг 4: Генерация эмбеддингов
    embeddings = embed_texts(texts)
    
    # Шаг 5: Создание векторного хранилища FAISS
    vectorstore = FAISS.from_texts([text.page_content for text in texts], embeddings)
    
    # Шаг 6: Загрузка векторного хранилища FAISS
    faiss_index_path = "faiss_index"
    vectorstore.save_local(faiss_index_path)
    retriever = vectorstore.as_retriever()
except Exception as e:
    print(f"Ошибка при загрузке данных: {e}")
    # Создаем пустое хранилище если возникла ошибка
    empty_texts = ["Данные отсутствуют"]
    empty_embeddings = np.zeros((1, 312))  # размерность должна соответствовать модели
    vectorstore = FAISS.from_texts(empty_texts, empty_embeddings)
    retriever = vectorstore.as_retriever()

# Функция для вызова вашего LLM через API
def call_llm_api(prompt):
    try:
        response = requests.post(LLM_API_ENDPOINT, json={"prompt": prompt}, timeout=30)
        if response.status_code == 200:
            return response.json().get("generated_text", "")
        else:
            print(f"Ошибка при обращении к LLM API: {response.status_code}")
            return "Извините, в данный момент я не могу обработать ваш запрос. Пожалуйста, попробуйте позже."
    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения с LLM API: {e}")
        return "Извините, в данный момент я не могу связаться с сервером. Пожалуйста, проверьте подключение и попробуйте позже."
    except Exception as e:
        print(f"Неизвестная ошибка при вызове LLM API: {e}")
        return "Произошла неизвестная ошибка. Пожалуйста, попробуйте позже."

# Основной шаблон для генерации ответов
template = """Ты - полезный помощник, который генерирует несколько поисковых запросов на основе предыдущего контекста переписки с пользователем и нового вопроса.
Предыдущий контекст: 
{context}
Генерируй несколько поисковых запросов, связанных с: {question}
Ответ (4 поисковых запроса):"""
prompt_rag_fusion = ChatPromptTemplate.from_template(template)


# Словарь с системными промптами для разных ролей
SYSTEM_PROMPTS = {
    "Ассистент-стилист": '''
    Ты ассистент-стилист. Твоя задача — собрать капсульный гардероб или подобрать несколько луков (с чем носить элемент одежды).
    Для каждого запроса:
    1. Задай уточняющие вопросы о стиле, предпочтениях, бюджете и случае использования.
    2. Используй свои знания о модных трендах и правилах сочетания одежды.
    3. Учитывай сезонность и климатические особенности.
    4. Предоставь нумерованный список предметов одежды с конкретными рекомендациями.
    5. Объясни, почему ты рекомендуешь именно эти предметы и как их сочетать.
    Всегда предоставляй ответ в виде четкого нумерованного списка одежды без лишних подробностей.
    
    Используй следующий контекст, чтобы лучше понять запрос пользователя:
    {context}
    ''',

    "Ассистент-косметолог": '''
    Ты ассистент-косметолог. Твоя задача — подобрать уход под тип кожи и образ жизни пользователя.
    Для каждого запроса:
    1. Задай уточняющие вопросы о типе кожи, проблемах, возрасте, аллергиях и бюджете.
    2. Используй свои знания о косметических ингредиентах и их воздействии на кожу.
    3. Учитывай сезонность и климатические особенности.
    4. Предлагай конкретные продукты и объясняй их действие.
    5. Учитывай совместимость продуктов между собой.
    Всегда структурируй ответ следующим образом: сначала дай общий совет по уходу за кожей, а затем предоставь нумерованный список конкретных средств ухода за кожей.
    
    Используй следующий контекст, чтобы лучше понять запрос пользователя:
    {context}
    ''',

    "Ассистент-нутрициолог": '''
    Ты ассистент-нутрициолог. Твоя задача — подобрать продуктовую корзину под КБЖУ и бюджет пользователя или ответить на вопрос о питании.
    Для каждого запроса:
    1. Задай уточняющие вопросы о целях питания, аллергиях, предпочтениях, бюджете и образе жизни.
    2. Используй свои знания о пищевой ценности продуктов и принципах здорового питания.
    3. Рассчитай примерное КБЖУ и распределение по приемам пищи.
    4. Предлагай конкретные продукты в рамках указанного бюджета.
    5. Учитывай сезонность и доступность продуктов.
    В конце ответа всегда предоставляй нумерованный список продуктов, которые нужно купить.
    
    Используй следующий контекст, чтобы лучше понять запрос пользователя:
    {context}
    ''',

    "Ассистент-дизайнер": '''
    Ты ассистент-дизайнер. Твоя задача — подобрать сезонный декор для дома или описать, как лучше обставить комнату от мебели до мелких деталей.
    Для каждого запроса:
    1. Задай уточняющие вопросы о стиле интерьера, размерах помещения, бюджете и предпочтениях.
    2. Используй свои знания о дизайне интерьера, сочетании цветов и материалов.
    3. Учитывай функциональность и эргономику пространства.
    4. Предлагай конкретные предметы мебели и декора.
    5. Объясни, как они будут сочетаться между собой.
    Сначала опиши общую концепцию и расстановку мебели, а затем предоставь нумерованный список мебели и декора, которые нужно приобрести.
    
    Используй следующий контекст, чтобы лучше понять запрос пользователя:
    {context}
    '''
}

# Default system prompt if role not specified
DEFAULT_SYSTEM_PROMPT = '''
Ты шопинг-ассистент. Твоя задача — помочь пользователю подобрать наиболее подходящие товары по оптимальным ценам, соответствующие его запросу, бюджету и предпочтениям.
Для каждого запроса:
1. Задай уточняющие вопросы для понимания потребностей пользователя.
2. Используй свои знания для подбора наиболее подходящих товаров.
3. Учитывай соотношение цены и качества.
4. Предоставь четкие рекомендации в виде списка.
5. Объясни свой выбор и предложи возможные альтернативы.

Используй следующий контекст, чтобы лучше понять запрос пользователя:
{context}
'''

class_1_prompt = '''Ты - модель, которая классифицирует запросы по следующим категориям шопинг-ассистента: ["Ассистент-стилист", "Ассистент-косметолог", "Ассистент-нутрициолог", "Ассистент-дизайнер", "Общий шопинг-запрос"]. Отнеси следующий вопрос к одной из категорий: {question}.'''

class_2_prompt = '''Ты - модель, которая определяет детали запроса в сфере шопинга и классифицирует запросы по следующим категориям:
["Подбор гардероба", "Модные тренды", "Стильные сочетания", "Капсульный гардероб", 
"Уход за кожей", "Проблемная кожа", "Антивозрастной уход", "Декоративная косметика",
"Здоровое питание", "Диетическое питание", "Спортивное питание", "Вегетарианство/Веганство",
"Дизайн интерьера", "Сезонный декор", "Перепланировка", "Мебель", "Аксессуары для дома",
"Бюджетные покупки", "Премиум товары", "Скидки и акции", "Отзывы о товарах"].
Определи, к какой категории относится следующий вопрос: {question}.'''

# Основной промпт для генерации ответов
system_prompt = DEFAULT_SYSTEM_PROMPT

main_prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{question}")])
class_1_template = ChatPromptTemplate.from_template(class_1_prompt)
class_2_template = ChatPromptTemplate.from_template(class_2_prompt)


def rag_fusion_pipeline(question):
    """
    Использует retriever для поиска наиболее релевантных документов,
    на основе которых формируется контекст для генерации ответа.
    """
    input_data = {"context": "", "question": question}
    prompt = prompt_rag_fusion.format(context="", question=question)

    # Запрос к LLM API для генерации дополнительных поисковых запросов
    multiple_queries = call_llm_api(prompt).split('\n')
    
    count = dict()
    for query in multiple_queries:
        if query.strip():  # Пропускаем пустые строки
            relevant_documents = retriever.invoke(query, k=4)
            relevant_documents_content = [page.page_content for page in relevant_documents]
            for content in relevant_documents_content:
                count[content] = count.get(content, 0) + 1

    # Сортировка фрагментов по релевантности
    sorted_chunks_for_rag_fusion = [doc for doc, _ in sorted(count.items(), key=lambda item: item[1], reverse=True)]

    # Объединение всех релевантных фрагментов в единый контекст
    joined_sorted_chunks_for_rag_fusion = "\n".join(sorted_chunks_for_rag_fusion)
    return joined_sorted_chunks_for_rag_fusion


def rag_chain(question):
    """
    Полная цепочка RAG: поиск релевантных документов и генерация ответа.
    """
    try:
        # Используем RAG для поиска релевантных документов
        joined_sorted_chunks_for_rag_fusion = rag_fusion_pipeline(question)
    
        # Сначала определяем категорию запроса для выбора подходящего ассистента
        role = classify(question, class_1_template)
        
        # Выбираем подходящий промпт в зависимости от категории
        if role in SYSTEM_PROMPTS:
            # Используем специализированный промпт
            role_prompt = SYSTEM_PROMPTS[role]
            role_template = ChatPromptTemplate.from_messages([("system", role_prompt), ("human", "{question}")])
            prompt = role_template.format(context=joined_sorted_chunks_for_rag_fusion, question=question)
        else:
            # Используем промпт по умолчанию (общий шопинг-ассистент)
            prompt = main_prompt.format(context=joined_sorted_chunks_for_rag_fusion, question=question)
    
        # Вызов вашего API с полным контекстом
        return call_llm_api(prompt)
    except Exception as e:
        print(f"Ошибка в функции rag_chain: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или сформулируйте запрос иначе."


def classify(question, template):
    try:
        prompt = template.format(question=question)
        return call_llm_api(prompt)
    except Exception as e:
        print(f"Ошибка в функции classify: {e}")
        return "Общий шопинг-запрос"  # возвращаем категорию по умолчанию в случае ошибки


@app.post("/predict")
async def predict_sentiment(request: Request):
    try:
        response_text = rag_chain(request.question)
        class_1 = classify(request.question, class_1_template)
        class_2 = classify(request.question, class_2_template)
        response = Response(answer=response_text, class_1=class_1, class_2=class_2)
        return response
    except Exception as e:
        print(f"Ошибка в endpoint predict: {e}")
        error_response = Response(
            answer="Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.",
            class_1="Ошибка",
            class_2="Ошибка"
        )
        return error_response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
