# query_engine.py — Traduction de questions en requêtes Elasticsearch

import json
import re
import requests
import urllib3
from openai import OpenAI
from config import ES_URL, ES_INDEX, ES_USER, ES_PASSWORD, NVIDIA_API_KEY, LLM_MODEL

urllib3.disable_warnings()


class ElasticsearchClient:

    def __init__(self):
        self.base_url = f"{ES_URL}/{ES_INDEX}"
        self.auth     = (ES_USER, ES_PASSWORD)

    def search(self, query: dict) -> list:
        resp = requests.post(
            f"{self.base_url}/_search",
            auth=self.auth, verify=False, json=query
        )
        if resp.status_code == 400:
            print(f"❌ Requête ES invalide : {resp.text[:300]}")
            return []
        resp.raise_for_status()
        data = resp.json()
        if "aggregations" in data:
            return self._extraire_aggs(data["aggregations"])
        return [h["_source"] for h in data.get("hits", {}).get("hits", [])]

    def _extraire_aggs(self, aggs: dict) -> list:
        resultats = []
        for nom, agg in aggs.items():
            # Agrégation métrique simple (sum, avg, value_count)
            if "value" in agg and "buckets" not in agg and "doc_count" not in agg:
                val = agg["value"]
                if val is not None:
                    resultats.append({nom: round(val, 2)})
            # Agrégation terms (buckets)
            elif "buckets" in agg:
                for bucket in agg["buckets"]:
                    item = {nom: bucket["key"], "count": bucket["doc_count"]}
                    for k, v in bucket.items():
                        if isinstance(v, dict) and "value" in v:
                            item[k] = round(v["value"] * 100, 1) if "taux" in k else round(v["value"], 2) if v["value"] is not None else None
                        elif isinstance(v, dict) and "buckets" in v:
                            for b in v["buckets"]:
                                sub = {k: b["key"], "count": b["doc_count"]}
                                for sk, sv in b.items():
                                    if isinstance(sv, dict) and "value" in sv:
                                        sub[sk] = round(sv["value"] * 100, 1) if "taux" in sk else round(sv["value"], 2) if sv["value"] is not None else None
                                resultats.append(sub)
                    if not any(isinstance(v, dict) and "buckets" in v for v in bucket.values()):
                        resultats.append(item)
            # Agrégation filter (doc_count + sous-aggs)
            elif "doc_count" in agg:
                for k, v in agg.items():
                    if isinstance(v, dict) and "buckets" in v:
                        for bucket in v["buckets"]:
                            item = {k: bucket["key"], "count": bucket["doc_count"]}
                            for sk, sv in bucket.items():
                                if isinstance(sv, dict) and "value" in sv:
                                    item[sk] = round(sv["value"] * 100, 1) if "taux" in sk else round(sv["value"], 2) if sv["value"] is not None else None
                            resultats.append(item)
        return resultats


class QueryTranslator:

    SCHEMA = """
Champs disponibles (text+keyword = utilisable avec .keyword pour les agrégations) :
- NRO (text+keyword)
- PLAQUE (text+keyword)
- Zone de couverture (text+keyword)
- commune (text+keyword)
- departement (text+keyword)
- region (text+keyword)
- ZONE DRV (text+keyword) : ex DRV1, DRV2, DRVN, DRVC
- status_dep (text+keyword) : LIVREE, EN TRAVAUX, EN DESIGN
- status_commune (text+keyword)
- programme (text+keyword)
- annee (text+keyword)
- mois_dep (text+keyword)
- taux_occupation (float) : entre 0 et 1
- brin_total (float)
- brin_occupe (float)
- concession (float)
- menage (float)
- population (float)
"""

    SYSTEM_PROMPT = f"""Tu es un expert Elasticsearch.
Traduis la question en une requête JSON Elasticsearch valide.
Retourne UNIQUEMENT le JSON, sans explication, sans markdown.
Si la question est générale (définition, explication), retourne : {{"general": true}}

Règles :
- Agrégations terms : TOUJOURS utiliser field.keyword (ex: "region.keyword")
- Champs numériques (taux_occupation, brin_total, etc.) : sans .keyword
- Questions de liste : "size": 1000
- Par défaut : "size": 100

{SCHEMA}

Exemples :
Question: "Quelles plaques sont EN TRAVAUX ?"
Réponse: {{"size": 1000, "query": {{"match": {{"status_dep": "EN TRAVAUX"}}}}}}

Question: "Quels NRO sont dans la région DAKAR avec taux > 50% ?"
Réponse: {{"size": 1000, "query": {{"bool": {{"must": [{{"match": {{"region": "DAKAR"}}}}, {{"range": {{"taux_occupation": {{"gt": 0.5}}}}}}]}}}}}}

Question: "Quelles zones ont un taux d'occupation supérieur à 50% ?"
Réponse: {{"size": 0, "query": {{"range": {{"taux_occupation": {{"gt": 0.5}}}}}}, "aggs": {{"par_zone": {{"terms": {{"field": "Zone de couverture.keyword", "size": 500}}, "aggs": {{"taux_moyen": {{"avg": {{"field": "taux_occupation"}}}}}}}}}}}}

Question: "Taux d'occupation par zone DRV ?"
Réponse: {{"size": 0, "aggs": {{"par_zone": {{"terms": {{"field": "ZONE DRV.keyword", "size": 50}}, "aggs": {{"taux_moyen": {{"avg": {{"field": "taux_occupation"}}}}}}}}}}}}

Question: "Taux d'occupation par région ?"
Réponse: {{"size": 0, "aggs": {{"par_region": {{"terms": {{"field": "region.keyword", "size": 50}}, "aggs": {{"taux_moyen": {{"avg": {{"field": "taux_occupation"}}}}}}}}}}}}

Question: "Quels sont les programmes GPON disponibles ?"
Réponse: {{"size": 0, "aggs": {{"programmes": {{"terms": {{"field": "programme.keyword", "size": 100}}}}}}}}

Question: "Quels sont les NRO disponibles ?"
Réponse: {{"size": 0, "aggs": {{"nros": {{"terms": {{"field": "NRO.keyword", "size": 500}}}}}}}}

Question: "Combien de plaques sont LIVREES dans la région DAKAR ?"
Réponse: {{"size": 0, "query": {{"bool": {{"must": [{{"match": {{"status_dep": "LIVREE"}}}}, {{"match": {{"region": "DAKAR"}}}}]}}}}, "aggs": {{"total": {{"value_count": {{"field": "PLAQUE.keyword"}}}}}}}}

Question: "Combien de brins sont disponibles au total ?"
Réponse: {{"size": 0, "aggs": {{"total_brins": {{"sum": {{"field": "brin_total"}}}}}}}}

Question: "Quelle est la population totale couverte ?"
Réponse: {{"size": 0, "aggs": {{"total_population": {{"sum": {{"field": "population"}}}}}}}}

Question: "Quelle zone couvre le plus de ménages ?"
Réponse: {{"size": 0, "aggs": {{"par_zone": {{"terms": {{"field": "Zone de couverture.keyword", "size": 1, "order": {{"total_menages": "desc"}}}}, "aggs": {{"total_menages": {{"sum": {{"field": "menage"}}}}}}}}}}}}

Question: "Nombre de ménages couverts par région ?"
Réponse: {{"size": 0, "aggs": {{"par_region": {{"terms": {{"field": "region.keyword", "size": 50}}, "aggs": {{"total_menages": {{"sum": {{"field": "menage"}}}}}}}}}}}}

Question: "c'est quoi un NRO ?"
Réponse: {{"general": true}}
"""

    def __init__(self, llm: OpenAI):
        self.llm = llm

    @staticmethod
    def _extraire_json(texte: str) -> str:
        match = re.search(r'\{.*\}', texte, re.DOTALL)
        return match.group(0) if match else texte

    def traduire(self, question: str) -> dict:
        requete_str = self._extraire_json(self._appeler_llm([
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user",   "content": question}
        ]))
        try:
            return json.loads(requete_str)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON invalide, correction en cours...")
            requete_str = self._extraire_json(self._appeler_llm([
                {"role": "system",    "content": self.SYSTEM_PROMPT},
                {"role": "user",      "content": question},
                {"role": "assistant", "content": requete_str},
                {"role": "user",      "content": f"JSON invalide : {e}. Retourne uniquement le JSON corrigé."}
            ]))
            return json.loads(requete_str)

    def _appeler_llm(self, messages: list) -> str:
        completion = self.llm.chat.completions.create(
            model=LLM_MODEL, messages=messages, temperature=0, max_tokens=512
        )
        return completion.choices[0].message.content.strip()


class ResponseGenerator:

    SYSTEM_PROMPT = (
        "Tu es un assistant expert FTTH. "
        "Réponds à la question en te basant uniquement sur les données fournies. "
        "Sois concis et précis."
    )

    def __init__(self, llm: OpenAI):
        self.llm = llm

    def generer_general(self, question: str) -> str:
        completion = self.llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en réseaux FTTH. Sois concis."},
                {"role": "user",   "content": question}
            ],
            temperature=0.2, max_tokens=1024
        )
        return completion.choices[0].message.content

    def generer(self, question: str, resultats: list) -> str:
        if not resultats:
            return "Aucun résultat trouvé pour cette question."

        vus, uniques = set(), []
        for doc in resultats:
            cle = json.dumps(doc, sort_keys=True, ensure_ascii=False)
            if cle not in vus:
                vus.add(cle)
                uniques.append(doc)

        # Formatage direct pour les résultats d'agrégation (taux, counts)
        # Évite que le LLM hallucine sur des listes de données structurées
        premier = uniques[0]
        champs_num = [k for k, v in premier.items() if isinstance(v, (int, float)) and k != "count"]
        champs_txt = [k for k, v in premier.items() if isinstance(v, str)]

        if champs_txt and champs_num:
            lignes = []
            for doc in uniques:
                label = doc.get(champs_txt[0], "")
                vals  = ", ".join(f"{k}: {doc[k]}%" if "taux" in k else f"{k}: {doc[k]:,}".replace(",", " ")
                                  for k in champs_num if doc.get(k) is not None)
                lignes.append(f"- {label} — {vals}")
            return f"{len(uniques)} résultat(s) :\n" + "\n".join(lignes)

        # Pour les documents complets, passer par le LLM
        contexte = "\n\n".join(
            "\n".join(f"{k}: {v}" for k, v in doc.items() if v not in [None, "-", ""])
            for doc in uniques[:200]
        )
        completion = self.llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": f"{self.SYSTEM_PROMPT}\n\nDonnées :\n{contexte}"},
                {"role": "user",   "content": question}
            ],
            temperature=0.2, max_tokens=1024
        )
        return completion.choices[0].message.content


class QueryEngine:

    def __init__(self):
        llm             = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
        self.es         = ElasticsearchClient()
        self.translator = QueryTranslator(llm)
        self.generator  = ResponseGenerator(llm)

    def run(self, question: str) -> str:
        print(f"\n❓ Question : {question}")
        print("🔄 Traduction en requête Elasticsearch...")
        try:
            requete = self.translator.traduire(question)
        except Exception as e:
            print(f"JSON invalide apres correction : {e}")
            return self.generator.generer_general(question)

        if requete.get("general"):
            print("💬 Question générale détectée...")
            reponse = self.generator.generer_general(question)
            print(f"\n💬 Réponse :\n{reponse}\n")
            return reponse

        print(f"📋 Requête générée :\n{json.dumps(requete, ensure_ascii=False, indent=2)}")
        print("🔍 Exécution sur Elasticsearch...")
        resultats = self.es.search(requete)
        print(f"✅ {len(resultats)} résultat(s) trouvé(s)")
        reponse = self.generator.generer(question, resultats)
        print(f"\n💬 Réponse :\n{reponse}\n")
        return reponse


if __name__ == "__main__":
    engine = QueryEngine()
    print("💬 FTTH Query Engine — posez vos questions (Ctrl+C pour quitter)\n")
    while True:
        try:
            question = input("❓ Votre question : ").strip()
            if question:
                engine.run(question)
                print("-" * 60)
        except KeyboardInterrupt:
            print("\nAu revoir !")
            break
