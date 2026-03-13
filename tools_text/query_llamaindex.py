import aiohttp
import json
from typing import Optional


class Tools:
    def __init__(self):
        self.base_url = "http://llamaindex:8000"

    async def query_llamaindex(self, query: str, doc_type: str = "pdf") -> str:
        """
        Задать вопрос по базе знаний (LlamaIndex).
        :param query: Вопрос к документам.
        :param doc_type: 'pdf' или 'code'.
        """

        url = f"{self.base_url}/query"
        # Передаем параметры в строку запроса (Query Params)
        params = {"q": query, "doc_type": doc_type, "top_k": 8}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, timeout=120) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return f"❌ Ошибка сервера (Status {response.status}): {error_text}"

                    data = await response.json()
                    answer = data.get("answer", "Ответ не получен")
                    sources = data.get("sources", [])

                    # Формируем красивый вывод с цитатами
                    result = f"💡 **Ответ:** {answer}\n\n"
                    if sources:
                        result += "---\n### Использованные источники:\n"
                        for i, src in enumerate(
                            sources[:2], 1
                        ):  # Берем первые 2 для краткости
                            score = (
                                f"(Score: {src['score']:.2f})"
                                if src.get("score")
                                else ""
                            )
                            result += f"**{i}.** {src['text'][:200]}... {score}\n"

                    return result

        except Exception as e:
            return f"❌ Ошибка соединения: {str(e)}"
