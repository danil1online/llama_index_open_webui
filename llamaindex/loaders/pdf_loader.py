from llama_index.core import SimpleDirectoryReader


def load_pdf_docs(path: str):
    return SimpleDirectoryReader(path, required_exts=[".pdf"]).load_data()