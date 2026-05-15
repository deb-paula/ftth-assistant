# ingest.py — Extraction ES → transformation → vectorisation → FAISS
# Usage : python ingest.py           (depuis Elasticsearch)
#         python ingest.py <url>     (depuis une URL ou PDF)

import sys
import os
import json
import requests
import faiss
import numpy as np
import urllib3
from io import BytesIO
from sentence_transformers import SentenceTransformer
from config import (
    ES_URL, ES_INDEX, ES_USER, ES_PASSWORD,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, FAISS_PATH
)

urllib3.disable_warnings()


class TextTransformer:
    """Transforme et découpe les textes avant vectorisation."""

    @staticmethod
    def source_vers_texte(src: dict) -> str:
        taux = src.get('taux_occupation')
        taux_str = f"{round(taux * 100, 1)}%" if taux is not None else '-'
        return (
            f"NRO: {src.get('NRO', '-')}\n"
            f"NRO de rattachement: {src.get('NRO de rattachement', '-')}\n"
            f"Plaque: {src.get('PLAQUE', '-')}\n"
            f"Zone de couverture: {src.get('Zone de couverture', '-')}\n"
            f"Commune: {src.get('commune', '-')}\n"
            f"Statut commune: {src.get('status_commune', '-')}\n"
            f"Département: {src.get('departement', '-')}\n"
            f"Région: {src.get('region', '-')}\n"
            f"Zone DRV: {src.get('ZONE DRV', '-')}\n"
            f"Statut déploiement: {src.get('status_dep', '-')}\n"
            f"Programme: {src.get('programme', '-')}\n"
            f"Année: {src.get('annee', '-')}\n"
            f"Mois déploiement: {src.get('mois_dep', '-')}\n"
            f"Concessions: {src.get('concession', '-')}\n"
            f"Ménages: {src.get('menage', '-')}\n"
            f"Population: {src.get('population', '-')}\n"
            f"Brin total: {src.get('brin_total', '-')}\n"
            f"Brin occupé: {src.get('brin_occupe', '-')}\n"
            f"Taux occupation: {taux_str}"
        )

    @staticmethod
    def chunker(texte: str) -> list:
        """Découpe un texte long (PDF/URL) par taille fixe."""
        chunks, start = [], 0
        while start < len(texte):
            chunks.append(texte[start:start + CHUNK_SIZE])
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return [c for c in chunks if c.strip()]

    @staticmethod
    def charger_url(url: str) -> str:
        # Télécharge une page web ou un PDF et retourne le texte brut
        resp = requests.get(url, timeout=15)
        if url.lower().endswith(".pdf"):
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(resp.content)).pages)
        else:
            from bs4 import BeautifulSoup
            return BeautifulSoup(resp.text, "html.parser").get_text(separator="\n")


class FAISSStore:
    """Gère le stockage et la lecture de l'index FAISS."""

    def __init__(self):
        self.index_file = os.path.join(FAISS_PATH, "index.faiss")
        self.docs_file  = os.path.join(FAISS_PATH, "docs.json")

    def charger(self):
        if os.path.exists(self.index_file) and os.path.exists(self.docs_file):
            with open(self.docs_file, "r", encoding="utf-8") as f:
                return faiss.read_index(self.index_file), json.load(f)
        return None, []

    def sauvegarder(self, textes: list, vecs: list, ecraser: bool = False):
        os.makedirs(FAISS_PATH, exist_ok=True)
        if ecraser:
            index, docs = None, []
        else:
            index, docs = self.charger()
        if index is None:
            index = faiss.IndexFlatL2(len(vecs[0]))
        index.add(np.array(vecs, dtype="float32"))
        docs.extend(textes)
        faiss.write_index(index, self.index_file)
        with open(self.docs_file, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False)
        print(f"✅ {len(textes)} documents insérés ({index.ntotal} total)")


class Vectorizer:
    """Encode les textes en vecteurs et les insère dans FAISS."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.store = FAISSStore()

    def vectoriser(self, textes: list, ecraser: bool = False):
        print(f"✂️  Vectorisation de {len(textes)} documents...")
        vecs = self.model.encode(textes, show_progress_bar=True).tolist()
        print("💾 Sauvegarde dans FAISS...")
        self.store.sauvegarder(textes, vecs, ecraser=ecraser)


class Ingester:
    """Orchestre l'ingestion depuis Elasticsearch ou une URL."""

    def __init__(self):
        self.transformer = TextTransformer()
        self.vectorizer  = Vectorizer()

    def depuis_elasticsearch(self):
        print("⚠️  Les données ES sont interrogées directement via QueryEngine.")
        print("ℹ️  Utilisez python ingest.py <url> pour indexer des documents externes.")

    def depuis_url(self, url: str):
        print(f"🌐 Chargement depuis {url}...")
        texte  = self.transformer.charger_url(url)
        chunks = self.transformer.chunker(texte)
        print(f"   → {len(chunks)} chunks extraits")
        self.vectorizer.vectoriser(chunks)


if __name__ == "__main__":
    ingester = Ingester()
    if len(sys.argv) > 1:
        ingester.depuis_url(sys.argv[1])
    else:
        ingester.depuis_elasticsearch()
