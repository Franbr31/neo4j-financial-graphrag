# 📊 SEC Knowledge Graph Generator for GraphRAG

This project extracts **financial filings (10-K)** from the **U.S. SEC EDGAR database** using the [sec-api](https://sec-api.io/), parses **XBRL data**, and builds a **knowledge graph in Neo4j** representing financial metrics over time.  
You can then query this graph directly or use it for **Graph-RAG (Retrieval Augmented Generation)** with a language model.

---

## 🚀 Features

- Extracts the **last 50 annual 10-K filings** for a given company (default: Apple Inc. – AAPL)
- Parses selected **financial metrics** (e.g., Revenue, Net Income, Assets, Cash)
- Builds a **property graph** in Neo4j using Cypher
- Supports future integration with **LLM-based GraphRAG pipelines**

---

## 📦 Tech Stack

| Component | Description |
|----------|-------------|
| `sec-api` | API wrapper to access EDGAR filings |
| `Neo4j` | Graph database to store structured metric entities |
| `Cypher` | Query language for building & querying the graph |
| `Python` | Core logic and orchestration |
| `lxml` | For parsing XBRL XML structures |

---

## 🧠 Graph Structure

Each company filing generates relationships like:

```
(:Company)-[:REPORTED]->(:MetricDate)
(:MetricDate)-[:HAS_VALUE]->(:Value)
(:MetricDate)-[:FOR_PERIOD]->(:Date)
(:MetricDate)-[:IN_UNITS]->(:Currency)
```

Example:
```
("Apple Inc.") -[:REPORTED]-> ("Revenue_2023-09-30")
("Revenue_2023-09-30") -[:HAS_VALUE]-> "383285000000"
```

---

## 📂 File Structure

```
.
├── sec_graph_loader.py       # Core ETL script
├── requirements.txt          # Dependencies
├── README.md                 # This file
```

---

## 🔧 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/sec-graph-rag.git
cd sec-graph-rag
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your environment variables

Create a `.env` file or export manually:
```env
SEC_API_KEY=your_sec_api_key
```

Or in your shell:
```bash
export SEC_API_KEY="your_sec_api_key"
```

> 🔐 You can get your free API key from [sec-api.io](https://sec-api.io/)

---

### 4. Start Neo4j

Ensure Neo4j is running locally:

```bash
docker run -d   --name neo4j-sec   -p7474:7474 -p7687:7687   -e NEO4J_AUTH=neo4j/your_password   neo4j:latest
```

---

### 5. Run the script

```bash
python sec_graph_loader.py
```

This will populate your Neo4j graph with 50 filings of AAPL and their metrics.

---

## 💡 Example Cypher Queries

### Top 5 Revenue values for Apple:
```cypher
MATCH (c:Entity)-[:REPORTED]->(m:Entity)
WHERE m.name STARTS WITH "Revenue"
MATCH (m)-[:HAS_VALUE]->(v:Entity)
RETURN m.name AS period, v.name AS revenue
ORDER BY toFloat(v.name) DESC
LIMIT 5
```

---

## 🧠 Use with GraphRAG

Once your graph is populated, you can use an LLM with **Cypher-guided retrieval** to:

- Query financial trends  
- Compare companies  
- Answer "Why" or "How" based on filings  

> You can plug this into LangChain or LlamaIndex for Cypher + RAG flows.

---

## 🛠️ To-Do / Ideas

- [ ] Support multi-company ingestion  
- [ ] Expand metric coverage via taxonomy discovery  
- [ ] Add embeddings for text fields (e.g., MD&A)  
- [ ] Integrate LangChain’s Graph-Cypher QA chain  

---

## 📄 License

MIT License