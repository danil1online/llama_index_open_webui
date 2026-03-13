import subprocess
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import CrossEncoder
from settings import SETTINGS, MODE


#def preload_ollama_model(model: str):
#    print(f"[PRELOAD] Pulling Ollama model: {model}")
#    try:
#        subprocess.run(["ollama", "pull", model], check=True)
#    except Exception as e:
#        print(f"[PRELOAD] Failed to pull Ollama model {model}: {e}")


def preload_hf_model(model: str):
    print(f"[PRELOAD] Downloading HF model: {model}")
    AutoModel.from_pretrained(model)
    AutoTokenizer.from_pretrained(model)


def preload_reranker(model: str):
    print(f"[PRELOAD] Downloading reranker: {model}")
    CrossEncoder(model)


if __name__ == "__main__":
    print(f"[PRELOAD] MODE={MODE}")

 #   if MODE == "ollama":
 #       preload_ollama_model(SETTINGS.embed_model_ollama)
 #   else:
 #       preload_hf_model(SETTINGS.embed_model_hf)
    preload_hf_model(SETTINGS.embed_model_hf)
    preload_reranker(SETTINGS.reranker_model)

    print("[PRELOAD] All models preloaded.")
