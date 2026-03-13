from qdrant_client import QdrantClient
from pydantic import BaseModel


class Tools:
    def __init__(self):
        # Адрес Qdrant внутри сети Docker
        self.qdrant_host = "http://qdrant:6333"

    async def clear_pdf_collection(self) -> str:
        """
        Полностью удалить коллекцию pdf_docs из векторной базы данных Qdrant.
        ВНИМАНИЕ: Это действие необратимо.
        """
        try:
            client = QdrantClient(self.qdrant_host)

            # Проверяем наличие коллекции перед удалением
            collections_res = client.get_collections()
            exists = any(c.name == "pdf_docs" for c in collections_res.collections)

            if exists:
                client.delete_collection(collection_name="pdf_docs")
                return "🗑️ Коллекция 'pdf_docs' успешно удалена. База знаний очищена."
            else:
                return "ℹ️ Коллекция 'pdf_docs' не найдена. База уже пуста."

        except Exception as e:
            return f"❌ Ошибка при очистке базы: {str(e)}"
