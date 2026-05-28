from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hakuryu Anti-Gravity"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:latest" # Default model
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT_SECONDS: float = 300.0

    # RAG
    RAG_DATA_DIR: str = "../docs/data"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "hakuryu_rag"
    RAG_TOP_K: int = 4

    # Staff
    STAFF_PIN: str = "1234"
    STAFF_PINS: str = "1:1111,2:2222,3:3333,4:4444,5:5555,6:6666,7:7777,8:8888,9:9999,10:1010,11:1112,12:1212,13:1313,14:1414,15:1515,16:1616,17:1717,18:1818,19:1919,20:2020,21:2121,22:2223,23:2323,24:2424,25:2525,26:2626,27:2727,28:2828,29:2929,30:3030"

    # Public wait-time mirror for GitHub Pages / Firebase Realtime Database.
    # Example: https://your-project-default-rtdb.firebaseio.com/publicWaitTimes.json
    FIREBASE_WAIT_TIMES_URL: str = ""
    FIREBASE_WAIT_TIMES_AUTH: str = ""
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
