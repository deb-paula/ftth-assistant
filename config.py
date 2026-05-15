import os
from dotenv import load_dotenv

load_dotenv()

ES_URL             = os.getenv("ES_URL",             "https://jambars-es.seetlu.orange-sonatel.com")
ES_INDEX           = os.getenv("ES_INDEX",           "jambars-assistant_ftth_v000")
ES_USER            = os.getenv("ES_USER",            "Debora")
ES_PASSWORD        = os.getenv("ES_PASSWORD",        "Sonatel@2026")

FAISS_PATH         = os.getenv("FAISS_PATH",         "./faiss_db")

EMBEDDING_MODEL    = os.getenv("EMBEDDING_MODEL",    "all-MiniLM-L6-v2")

NVIDIA_API_KEY     = os.getenv("NVIDIA_API_KEY",     "")
LLM_MODEL          = os.getenv("LLM_MODEL",          "meta/llama-3.1-8b-instruct")

CHUNK_SIZE         = int(os.getenv("CHUNK_SIZE",     "500"))
CHUNK_OVERLAP      = int(os.getenv("CHUNK_OVERLAP",  "50"))

FLASK_PORT         = int(os.getenv("FLASK_PORT",     "5000"))
FLASK_DEBUG        = os.getenv("FLASK_DEBUG",        "false").lower() == "true"
