from llama_index.core import SimpleDirectoryReader

EXTS = [
    ".py", ".cpp", ".cc", ".hpp", ".h", ".cs",
    ".js", ".ts", ".tsx", ".sql", ".json", ".yml", ".yaml", ".md", ".txt"
]


def load_code_docs(path: str):
    return SimpleDirectoryReader(path, required_exts=EXTS).load_data()