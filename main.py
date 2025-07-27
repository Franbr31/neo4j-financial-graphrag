from sec_api import QueryApi
from neo4j import GraphDatabase
from arelle import Cntlr, ModelManager
import requests
import os
import time

# === Configuración ===
SEC_API_KEY = os.getenv("SEC_API_KEY")  # o escribe tu API key aquí
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
TICKER = "AAPL"
LIMIT = 50
ORDER = "desc"  # Orden de los filings

queryApi = QueryApi(api_key=SEC_API_KEY)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# === Obtener los 50 últimos filings 10-K ===
filings = queryApi.get_filings({
    "query": f"ticker:{TICKER}",
    "from": "0",
    "size": LIMIT,
    "sort": [{ "filedAt": { "order": ORDER }}]
})

filings = filings.get("filings", [])

# === Configurar Arelle ===
cntlr = Cntlr.Cntlr()
model_manager = ModelManager.initialize(cntlr)

for filing in filings:
    company = filing.get("companyName", "Unknown Company")
    cik = filing.get("cik", None)
    ticker = filing.get("ticker", None)
    filed_at = filing.get("filedAt", None)
    form_type = filing.get("formType", None)
    period = filing.get("periodOfReport", None)
    data_files = filing.get("dataFiles", [])
    accession = filing.get("accessionNo", None)

    xbrl_url = next((f["documentUrl"] for f in data_files if f.get("type") == "XML"), None)
    if not xbrl_url:
        print(f"⚠️ No XML en {accession}")
        continue

    print(f"📥 Procesando: {accession} - {period}")
    try:
        # Descargar el archivo XML
        response = requests.get(xbrl_url)
        response.raise_for_status()
        xml_path = f"/tmp/{accession}.xml"
        with open(xml_path, "wb") as file:
            file.write(response.content)

        # Usar Arelle para procesar el archivo
        model_xbrl = model_manager.load(xml_path)
        triplets = [
            (company, "filed_form", form_type),
            (company, "accession", accession),
            (company, "reporting_period", period)
        ]

        # Extraer métricas usando Arelle
        for fact in model_xbrl.facts:
            label = fact.qname.localName
            value = fact.value
            context_ref = fact.contextID
            units = fact.unitID or "USD"
            date = period  # Puedes ajustar esto si necesitas más precisión

            metric_node = f"{label}_{date}"
            triplets += [
                (company, "reported", metric_node),
                (metric_node, "has_value", value),
                (metric_node, "for_period", date),
                (metric_node, "in_units", units)
            ]

    except Exception as e:
        print(f"❌ Error procesando XBRL: {e}")
        continue

    # === Guardar en Neo4j ===
    def add_triplet(tx, head, rel, tail):
        tx.run("""
            MERGE (a:Entity {name: $head})
            MERGE (b:Entity {name: $tail})
            MERGE (a)-[r:%s]->(b)
        """ % rel.upper(), head=head, tail=tail)

    with driver.session() as session:
        for h, r, t in triplets:
            session.write_transaction(add_triplet, h, r, t)

    time.sleep(0.5)  # para evitar límite de la API

print("✅ Grafo cargado con los últimos 50 reportes.")
