import json


def parse_args(args):
    if isinstance(args, str):
        try:
            return json.loads(args)
        except:
            return {"value": args}
    if isinstance(args, dict):
        return args
    return {"value": str(args)}


class Tools:
    async def echo(self, args):
        parsed = parse_args(args)
        return f"Тип: {type(parsed).__name__}\nЗначение: {parsed}"
