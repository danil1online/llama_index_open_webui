import os
import shutil
import mimetypes
import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# LlamaIndex 0.10+ использует пространство имен llama_index.core
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
#from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
#from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from llama_index.llms.openai_like import OpenAILike
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader
from tree_sitter_languages import get_parser

from settings import MODE, SETTINGS

app = FastAPI(title="LlamaIndex RAG Server")

# -----------------------------
# Глобальные настройки (Global Settings)
# -----------------------------

# Настройка LLM
#Settings.llm = Ollama(
#    model=SETTINGS.llm_model,
#    base_url=SETTINGS.ollama_url,
#    request_timeout=120.0  # Увеличиваем таймаут для локальных моделей
#)
Settings.llm = OpenAILike(
    
    # Если выбрали LM Studio
    #model="qwen3.5-4b", # Имя должно совпадать с тем, что выдает `lms status`
    #api_base="http://host.docker.internal:1234/v1",
    
    # Если выбрали Ollama
    #model="qwen3.5:4b",
    #api_base="http://host.docker.internal:11434/v1",

    # Если выбрали llama.cpp
    model="Qwen3.5-4B-Q4_K_M.gguf", # Имя должно совпадать
    api_base="http://host.docker.internal:8080/v1",
    
    api_key="lm-studio",
    is_chat_model=True,
    context_window=32768, # Явно укажите размер окна
    request_timeout=120.0
)


# Настройка Embeddings
#if MODE == "ollama":
#    Settings.embed_model = OllamaEmbedding(
#        model_name=SETTINGS.embed_model_ollama,
#        base_url=SETTINGS.ollama_url
#    )
#else:
#    Settings.embed_model = HuggingFaceEmbedding(
#        model_name=SETTINGS.embed_model_hf
#    )
    
Settings.embed_model = HuggingFaceEmbedding(
    model_name=SETTINGS.embed_model_hf
    )

Settings.chunk_size = 1024
Settings.chunk_overlap = 100

# Реранкер как Postprocessor
reranker = SentenceTransformerRerank(
    model=SETTINGS.reranker_model, 
    top_n=3  # Оставляем 3 самых релевантных узла после реранкинга
)

# Вместо простого вызова CodeSplitter(language="python"), 
# мы сами берем парсер и передаем его внутрь.
try:
    python_parser = get_parser("python")
    python_splitter = CodeSplitter(
        language="python",
        parser=python_parser, # Передаем объект парсера явно
        chunk_lines=40,
        chunk_lines_overlap=10,
        max_chars=1500
    )
except Exception as e:
    print(f"Ошибка инициализации CodeSplitter: {e}")
    # Фолбек на обычный парсер, если tree-sitter все равно не завелся
    from llama_index.core.node_parser import SentenceSplitter
    python_splitter = SentenceSplitter(chunk_size=1024)

# Клиенты Qdrant
qdrant_client = QdrantClient(url=SETTINGS.qdrant_url)
async_qdrant_client = AsyncQdrantClient(url=SETTINGS.qdrant_url)

# -----------------------------
# Utils
# -----------------------------

def detect_file_type(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    if ext == ".pdf": return "pdf"
    if ext in [".py", ".cpp", ".js", ".ts", ".sql", ".json", ".yml"]: return "code"
    return "text"

def ensure_collection(name: str):
    collections = qdrant_client.get_collections().collections
    if not any(c.name == name for c in collections):
        print(f"[INFO] Creating collection: {name}")
        # Получаем размер эмбеддинга для инициализации
        sample_dim = len(Settings.embed_model.get_text_embedding("test"))
        qdrant_client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=sample_dim, distance=Distance.COSINE)
        )

def get_vector_store(collection: str):
    ensure_collection(collection)
    return QdrantVectorStore(
        client=qdrant_client,
        aclient=async_qdrant_client,
        collection_name=collection
    )

# -----------------------------
# Endpoints
# -----------------------------

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    base = Path("/data/uploads")
    base.mkdir(parents=True, exist_ok=True)

    dest = base / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "status": "uploaded",
        "filename": file.filename,
        "type": detect_file_type(dest)
    }

@app.post("/index")
async def index_docs(doc_type: Optional[str] = None):
    base = Path("/data/uploads")
    if not base.exists() or not any(base.iterdir()):
        raise HTTPException(status_code=400, detail="No files to index")

    # 1. Автоматическое определение типа
    if not doc_type:
        first_file = next(base.iterdir())
        # Ваша функция detect_file_type
        doc_type = detect_file_type(first_file)

    collection = SETTINGS.collection_pdf if doc_type == "pdf" else SETTINGS.collection_code
    
    # 2. Загрузка данных
    reader = SimpleDirectoryReader(str(base))
    documents = reader.load_data()

    # 3. ВЫБОР ПАРСЕРА (Самая важная часть)
    if doc_type == "code":
        # Используем умный парсер для кода
        parser = CodeSplitter(
            language="python", # tree-sitter будет искать структуры Python
            chunk_lines=40,    # Пытаемся держать функции целиком
            chunk_lines_overlap=10,
            max_chars=1500
        )
    else:
        # Обычный текстовый парсер для PDF
        parser = SentenceSplitter(
            chunk_size=1024,
            chunk_overlap=200
        )

    # 4. Разбиваем документы на узлы вручную
    nodes = parser.get_nodes_from_documents(documents)

    # 5. Инициализация хранилища и индексация через Nodes
    vector_store = get_vector_store(collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Используем from_vector_store или создаем индекс из узлов
    VectorStoreIndex(
        nodes, # Передаем уже нарезанные узлы, а не документы
        storage_context=storage_context,
        show_progress=True
    )

    # 6. Очистка временной папки (чтобы файлы не накапливались для следующего раза)
    for file in base.iterdir():
        file.unlink()

    return {
        "status": "indexed", 
        "nodes_count": len(nodes), 
        "doc_type": doc_type, 
        "collection": collection
    }

@app.post("/query")
async def query(q: str, doc_type: Optional[str] = None, top_k: int = 8):
    # Определяем коллекцию
    uploads = Path("/data/uploads")
    if not doc_type:
        if not uploads.exists() or not any(uploads.iterdir()):
            collection = SETTINGS.collection_pdf # дефолт
        else:
            doc_type = detect_file_type(next(uploads.iterdir()))
            collection = SETTINGS.collection_pdf if doc_type == "pdf" else SETTINGS.collection_code
    else:
        collection = SETTINGS.collection_pdf if doc_type == "pdf" else SETTINGS.collection_code

    vector_store = get_vector_store(collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Настройка Query Engine с реранкером
    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        node_postprocessors=[reranker],
        streaming=False
    )

    # Асинхронный запрос к LLM
    response = await query_engine.aquery(q)

    return JSONResponse({
        "answer": str(response),
        "sources": [
            {
                "text": node.node.get_content()[:500],
                "score": float(node.score or 0),
                "metadata": node.node.metadata
            }
            for node in response.source_nodes
        ]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
