from sec_api import QueryApi
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde .env

# 👉 CONFIGURACIÓN
SEC_API_KEY = os.getenv("SEC_API_KEY")  # o escribe tu clave aquí
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
TICKER = "AAPL"
FROM = 0
LIMIT = 50
ORDER = "desc"

# Metricas a extraer
metrics = {
    "Revenue": "us-gaap:Revenues",
    "NetIncome": "us-gaap:NetIncomeLoss",
    "Assets": "us-gaap:Assets",
    "Cash": "us-gaap:CashAndCashEquivalentsAtCarryingValue"
}


def get_context_info(tree, context_id):
    ctx = tree.find(f".//context[@id='{context_id}']")
    if ctx is not None:
        end_date = ctx.find(".//endDate")
        if end_date is not None:
            return end_date.text
    return None

def add_triplet(tx, head, rel, tail):
    tx.run("""
        MERGE (a:Entity {name: $head})
        MERGE (b:Entity {name: $tail})
        MERGE (a)-[r:%s]->(b)
    """ % rel.upper(), head=head, tail=tail)


# 1. Obtener último filing 10-K
queryApi = QueryApi(api_key=SEC_API_KEY)
filings = queryApi.get_filings({
    "query": f"ticker:{TICKER} AND formType:10-K",
    "from": FROM,
    "size": LIMIT,
    "sort": [{ "filedAt": { "order": ORDER }}]
})['filings']


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

for filing in filings:

    # 2. Extraer datos clave
    company = filing["companyName"]
    ticker = filing["ticker"]
    filed_at = filing["filedAt"]
    form_type = filing["formType"]
    period = filing["periodOfReport"]
    data_files = filing.get("dataFiles", [])
    accession = filing["accessionNo"]

    # 3. Crear tripletas simples
    triplets = [
        (company, "filed_form", form_type),
        (company, "has_ticker", ticker),
        (form_type, "filed_on", filed_at),
        (form_type, "reporting_period", period),
        (company, "accession", accession)
    ]

    # 4. Agregar enlaces a documentos XBRL
    for file in data_files:
        desc = file.get("description", "").strip()
        url = file.get("documentUrl")
        doc_type = file.get("type")
        if url and desc:
            triplets.append((company, f"has_document_{doc_type}", url))




    def add_triplet(tx, h, rel, t):
        tx.run("""
            MERGE (a:Entity {name: $h})
            MERGE (b:Entity {name: $t})
            MERGE (a)-[r:%s]->(b)
        """ % rel.replace("-", "_").replace(".", "_").upper(), h=h, t=t)

    with driver.session() as session:
        for h, r, t in triplets:
            session.write_transaction(add_triplet, h, r, t)

    print("✅ Grafo generado exitosamente en Neo4j.")
