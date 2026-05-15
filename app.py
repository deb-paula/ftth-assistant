import os
import json
import faiss
import numpy as np
import requests as req
from io import BytesIO
from flask import Flask, render_template, request, jsonify
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from config import (
    FAISS_PATH, EMBEDDING_MODEL,
    NVIDIA_API_KEY, LLM_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP,
    FLASK_PORT, FLASK_DEBUG
)
from query_engine import QueryEngine

app = Flask(__name__)


class FAISSStore:
    """Gère la lecture et l'écriture de l'index FAISS."""

    def __init__(self):
        self.index_file = os.path.join(FAISS_PATH, "index.faiss")
        self.docs_file  = os.path.join(FAISS_PATH, "docs.json")

    def charger(self):
        if os.path.exists(self.index_file) and os.path.exists(self.docs_file):
            with open(self.docs_file, "r", encoding="utf-8") as f:
                return faiss.read_index(self.index_file), json.load(f)
        return None, []

    def sauvegarder(self, textes: list, vecs: list) -> int:
        os.makedirs(FAISS_PATH, exist_ok=True)
        index, docs = self.charger()
        if index is None:
            index = faiss.IndexFlatL2(len(vecs[0]))
        index.add(np.array(vecs, dtype="float32"))
        docs.extend(textes)
        faiss.write_index(index, self.index_file)
        with open(self.docs_file, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False)
        return len(textes)


class Retriever:
    """Recherche les documents les plus pertinents dans FAISS."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.store = FAISSStore()

    def rechercher(self, question: str, k: int = 3) -> list:
        index, docs = self.store.charger()
        if not index or index.ntotal == 0:
            return []
        vec = self.model.encode([question]).astype("float32")
        _, idx = index.search(vec, k)
        return [docs[i] for i in idx[0] if i < len(docs)]

    def inserer(self, texte: str) -> int:
        chunks = self._chunker(texte)
        vecs   = self.model.encode(chunks).tolist()
        return self.store.sauvegarder(chunks, vecs)

    def _chunker(self, texte: str) -> list:
        chunks, start = [], 0
        while start < len(texte):
            chunks.append(texte[start:start + CHUNK_SIZE])
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return [c for c in chunks if c.strip()]


class ChatEngine:
    """Génère une réponse via NVIDIA NIM à partir du contexte FAISS."""

    def __init__(self):
        self.llm       = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
        self.retriever = Retriever()

    def repondre(self, question: str) -> str:
        resultats = self.retriever.rechercher(question)
        messages  = []
        if resultats:
            messages.append({
                "role": "system",
                "content": (
                    "Tu es un assistant expert FTTH. Réponds uniquement à partir du contexte. "
                    "Si la réponse n'est pas dans le contexte, dis-le clairement.\n\n"
                    "Contexte :\n" + "\n\n".join(resultats)
                )
            })
        messages.append({"role": "user", "content": question})
        completion = self.llm.chat.completions.create(
            model=LLM_MODEL, messages=messages, temperature=0.2, max_tokens=1024
        )
        return completion.choices[0].message.content


class DocumentLoader:
    """Charge et extrait le texte depuis un fichier ou une URL."""

    @staticmethod
    def depuis_fichier(chemin: str) -> str:
        if chemin.endswith(".pdf"):
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(chemin).pages)
        with open(chemin, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def depuis_url(url: str) -> str:
        resp = req.get(url, timeout=15)
        if url.lower().endswith(".pdf"):
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(resp.content)).pages)
        from bs4 import BeautifulSoup
        return BeautifulSoup(resp.text, "html.parser").get_text(separator="\n")


# Instances globales
_chat_engine  = ChatEngine()
_query_engine = QueryEngine()
_retriever    = _chat_engine.retriever
_loader       = DocumentLoader()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stats")
def stats():
    import requests as req2
    import urllib3; urllib3.disable_warnings()
    from config import ES_URL, ES_INDEX, ES_USER, ES_PASSWORD
    try:
        raw = req2.post(
            f"{ES_URL}/{ES_INDEX}/_search",
            auth=(ES_USER, ES_PASSWORD), verify=False,
            json={"size": 0, "aggs": {
                "total_brins":   {"sum": {"field": "brin_total"}},
                "brins_occupes": {"sum": {"field": "brin_occupe"}},
                "taux_moyen":    {"avg": {"field": "taux_occupation"}},
                "total_plaques": {"cardinality": {"field": "PLAQUE.keyword"}},
                "par_statut":    {"terms": {"field": "status_dep.keyword", "size": 10}},
                "par_region":    {"terms": {"field": "region.keyword", "size": 20},
                                  "aggs": {"taux": {"avg": {"field": "taux_occupation"}}}},
                "top_zones":     {"terms": {"field": "Zone de couverture.keyword", "size": 5,
                                            "order": {"taux": "desc"}},
                                  "aggs": {"taux": {"avg": {"field": "taux_occupation"}}}},
                "par_drv":       {"terms": {"field": "ZONE DRV.keyword", "size": 10},
                                  "aggs": {"taux": {"avg": {"field": "taux_occupation"}}}}
            }}
        )
        if raw.status_code == 400:
            print(f"STATS ES erreur 400 : {raw.text[:500]}")
            return jsonify({"error": raw.text[:200]}), 500
        raw = raw.json()
        aggs = raw.get("aggregations", {})
        total_brins   = int(aggs.get("total_brins",   {}).get("value") or 0)
        brins_occupes = int(aggs.get("brins_occupes", {}).get("value") or 0)
        taux_moyen    = round((aggs.get("taux_moyen", {}).get("value") or 0) * 100, 1)
        total_plaques = aggs.get("total_plaques", {}).get("value", 0)
        total_docs    = raw.get("hits", {}).get("total", {}).get("value", 0)
        par_statut = [{"label": b["key"], "count": b["doc_count"]} for b in aggs.get("par_statut", {}).get("buckets", [])]
        par_region = [{"label": b["key"], "taux": round((b.get("taux", {}).get("value") or 0) * 100, 1)} for b in aggs.get("par_region", {}).get("buckets", [])]
        top_zones  = [{"label": b["key"], "taux": round((b.get("taux", {}).get("value") or 0) * 100, 1)} for b in aggs.get("top_zones", {}).get("buckets", [])]
        par_drv    = [{"label": b["key"], "taux": round((b.get("taux", {}).get("value") or 0) * 100, 1)} for b in aggs.get("par_drv",    {}).get("buckets", [])]
        return jsonify({"total_docs": total_docs, "total_plaques": total_plaques, "total_brins": total_brins,
                        "brins_occupes": brins_occupes, "brins_libres": total_brins - brins_occupes,
                        "taux_moyen": taux_moyen, "par_statut": par_statut, "par_region": par_region,
                        "top_zones": top_zones, "par_drv": par_drv})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")
    mode     = request.json.get("mode", "faiss")  # "faiss" ou "elasticsearch"
    if not question:
        return jsonify({"error": "Question vide"}), 400
    
    if mode == "elasticsearch":
        reponse = _query_engine.run(question)
    else:
        reponse = _chat_engine.repondre(question)
    
    return jsonify({"reponse": reponse})


@app.route("/upload", methods=["POST"])
def upload():
    os.makedirs("docs", exist_ok=True)
    fichier = request.files["file"]
    chemin  = os.path.join("docs", fichier.filename)
    fichier.save(chemin)
    nb = _retriever.inserer(_loader.depuis_fichier(chemin))
    return jsonify({"message": f"{fichier.filename} indexé ({nb} chunks)"})


@app.route("/load_url", methods=["POST"])
def load_url():
    url = request.json.get("url", "")
    if not url:
        return jsonify({"error": "URL vide"}), 400
    nb = _retriever.inserer(_loader.depuis_url(url))
    return jsonify({"message": f"URL indexée ({nb} chunks)"})


if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)


    
