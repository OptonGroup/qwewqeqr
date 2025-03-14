from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    """
    Настраивает CORS для FastAPI приложения
    """
    origins = [
        "http://localhost:3000",       # Локальный фронтенд
        "http://frontend:3000",        # Контейнер фронтенда в Docker
        "http://localhost:8000",       # Локальный бэкенд
        "http://backend:8000",         # Контейнер бэкенда в Docker
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app 