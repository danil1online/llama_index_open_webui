import aiohttp
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import os


class Tools:
    class Valves(BaseModel):
        OPEN_WEBUI_API_KEY: str = Field(
            default="", description="Ваш API Key из настроек профиля Open WebUI"
        )

    def __init__(self):
        self.base_url = "http://llamaindex:8000"
        self.valves = self.Valves()

    async def process_and_upload_file(
        self, file_id: str, doc_type: str, __metadata__: dict
    ) -> str:
        """
        Загрузить файл в систему LlamaIndex для анализа (добавление в базу).
        :param file_id: UUID файла из Open WebUI.
        :param doc_type: 'pdf' или 'code'.
        """
        # Настройка таймаутов: 30 минут на тяжелую индексацию
        timeout_index = aiohttp.ClientTimeout(total=1800)
        timeout_standard = aiohttp.ClientTimeout(total=120)

        # 1. Формируем заголовки авторизации
        request_headers = {}
        if self.valves.OPEN_WEBUI_API_KEY:
            request_headers["Authorization"] = (
                f"Bearer {self.valves.OPEN_WEBUI_API_KEY}"
            )
        elif __metadata__.get("token"):
            request_headers["Authorization"] = f"Bearer {__metadata__['token']}"
        else:
            return "❌ Ошибка: API ключ не задан в настройках инструмента (Valves)."

        ow_url = f"http://open-webui:8080/api/v1/files/{file_id}/content"

        try:
            async with aiohttp.ClientSession() as session:
                # 2. Скачиваем файл
                async with session.get(
                    ow_url, headers=request_headers, timeout=timeout_standard
                ) as response:
                    if response.status != 200:
                        return f"❌ Ошибка WebUI (Status {response.status})"
                    file_content = await response.read()

                # 3. Отправляем в LlamaIndex
                data = aiohttp.FormData()
                data.add_field("file", file_content, filename=f"document.{doc_type}")

                async with session.post(
                    f"{self.base_url}/upload", data=data, timeout=timeout_standard
                ) as upload_r:
                    if upload_r.status != 200:
                        return f"❌ Ошибка LlamaIndex Upload (Status {upload_r.status})"

                # 4. Запускаем индексацию (E5-Large + Qdrant)
                async with session.post(
                    f"{self.base_url}/index",
                    params={"doc_type": doc_type},
                    timeout=timeout_index,
                ) as index_r:
                    if index_r.status != 200:
                        return (
                            f"❌ Ошибка индексации. Проверьте логи сервера LlamaIndex."
                        )

            return f"✅ Файл {file_id} успешно добавлен в базу знаний."

        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
