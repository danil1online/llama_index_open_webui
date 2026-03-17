import os
from pydantic import BaseModel


class Settings(BaseModel):
    mode: str = os.getenv("MODE", "hf")  # hf | ollama

#    ollama_url: str = os.getenv("OLLAMA_URL", "http://ollama:11434")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333")

    collection_pdf: str = os.getenv("COLLECTION_PDF", "pdf_docs")
    collection_code: str = os.getenv("COLLECTION_CODE", "code_docs")

    # Настройки для LM
    # host.docker.internal позволит контейнеру достучаться до lms на хосте
    
    # Если выбрали вариант LM Studio
    #lms_url: str = os.getenv("LMS_URL", "http://host.docker.internal:1234/v1")
    #llm_model: str = os.getenv("LLM_MODEL", "qwen3.5-4b")
    
    # Если выбрали вариант Ollama-docker
    #lms_url: str = os.getenv("LMS_URL", "http://host.docker.internal:11434/v1")
    #llm_model: str = os.getenv("LLM_MODEL", "qwen3.5:4b")

    # Если выбрали вариант llama.cpp
    lms_url: str = os.getenv("LMS_URL", "http://host.docker.internal:8080/v1")
    llm_model: str = os.getenv("LLM_MODEL", "Qwen3.5-4B-Q4_K_M.gguf")

    embed_model_hf: str = os.getenv("EMBED_MODEL_HF", "intfloat/multilingual-e5-large")

    reranker_model: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")


SETTINGS = Settings()
MODE = SETTINGS.mode
