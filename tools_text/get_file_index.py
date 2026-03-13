import json
import re


def parse_args(args):
    if isinstance(args, str):
        try:
            return json.loads(args)
        except:
            # Ищем UUID (36 символов: буквы, цифры и дефисы)
            match = re.search(r"[0-9a-fA-F-]{36}", args)
            if match:
                return {"file_id": match.group(0)}
            # Если это имя файла, а не ID, возвращаем как есть для отладки
            return {"file_name": args}
    if isinstance(args, dict):
        return args
    return {"value": str(args)}


class Tools:
    async def get_file_index(self, args: str):
        """
        Используй этот инструмент для получения системного ID файла.
        Передавай сюда ID файла или его полное описание.
        """
        parsed = parse_args(args)

        # В Open WebUI доступ к индексам файлов обычно идет через объект __metadata__
        # или через специальные API вызовы, если этот Tool имеет к ним доступ.

        return f"Инструмент получил данные: {parsed}. Для индексации в БД требуется UUID файла."
