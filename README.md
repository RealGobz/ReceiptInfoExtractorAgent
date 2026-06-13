# ReceiptInfoExtractorAgent

> AI-Powered Financial Compliance Auditor for the Banking Sector

**ReceiptInfoExtractorAgent** is an autonomous AI pipeline designed to ingest unstructured, messy financial logs and enforce strict formatting. Built to streamline compliance auditing (including adherence to SAMA regulatory standards), the system ensures zero conversational garbage leaks into the structured ledger.

---

## 🧠 Core Architecture

The agent operates on a robust four-stage pipeline:

1. **Multi-Model Inference Engine** — Supports both cloud-hosted (Anthropic Claude 3.5 Sonnet) and local, privacy-first models (Ollama / Llama 3.1).
2. **Strict Schema Enforcement** — Utilizes LangChain and Pydantic `.with_structured_output()` to force the model to output valid JSON matching an exact enterprise schema.
3. **Agentic Self-Correction Loop** — If the LLM misses a field or hallucinates, Pydantic throws a `ValidationError`. The agent catches this, rewrites the prompt programmatically with the exact error traceback, and feeds it back to the model to self-correct — without crashing the pipeline.
4. **Local Business Logic Auditor** — Successfully parsed data is immediately passed through a local Python tool (`flag_discrepancy`) to detect anomalies (e.g., transactions exceeding allowances or missing critical timestamp data).

---

## ⚙️ Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) installed *(if running local models)*
- Anthropic API Key *(if running Claude)*

---

## 🚀 Installation

**1. Clone the repository:**

```bash
git clone https://github.com/RealGobz/ReceiptInfoExtractorAgent.git
cd ReceiptInfoExtractorAgent
```

**2. Set up a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies:**

```bash
pip install langchain-anthropic langchain-ollama langchain-core pydantic streamlit
```

**4. Configure environment variables:**

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

---

## 💻 Usage

```python
from receipt_info_extractor_agent import ReceiptInfoExtractorAgent

# 1. Initialize the auditor agent
#    Choose 'ollama' for local inference or 'claude' for cloud
auditor = ReceiptInfoExtractorAgent(
    session_id="audit_run_001",
    provider="ollama",
    model_id="llama3.1"
)

# 2. Feed it unstructured, messy data
messy_log = "Paid AWS 500 SAR yesterday for the new server hosting, lost the invoice."

# 3. Execute extraction with the self-correction loop
result = auditor.extract_with_recovery(messy_log, max_retries=3)

# 4. View structured compliance output and flagged anomalies
print(result)
```

### Expected Output

The system returns a dictionary containing:

| Key | Description |
|-----|-------------|
| `status` | `"success"`, `"failed"`, or `"error"` |
| `data` | Perfectly formatted, schema-compliant receipt data |
| `attempts_required` | Number of LLMOps self-correction retries used |
| `anomalies_found` | List of business logic flags raised (e.g., amount overages, missing timestamps) |

---

## 🗂️ Data Schema

Each extracted receipt conforms to the following Pydantic model:

| Field | Type | Description |
|-------|------|-------------|
| `vendor` | `str` | Name of the vendor (e.g., `"Amazon"`) |
| `amount` | `float` | Total amount spent |
| `currency` | `str` | Currency code (e.g., `"SAR"`, `"USD"`) |
| `date` | `str \| None` | Transaction date in ISO 8601 format (`YYYY-MM-DD`) |
| `category` | `str` | Purchase category (e.g., `"Utilities"`) |

---

## 🚩 Business Logic Flags

The local `flag_discrepancy` auditor raises flags for:

- **Amount > 10,000** — Transaction exceeds the maximum single-entry corporate allowance.
- **Missing date** — Audit trails require a valid ISO timestamp.

---

## 🔧 Git Setup

**If updating an existing repo:**

```bash
git add .
git commit -m "chore: rename project, class, and documentation to ReceiptInfoExtractorAgent"
git remote set-url origin https://github.com/RealGobz/ReceiptInfoExtractorAgent.git
git push origin main
```

**If initializing from scratch:**

```bash
git init
git add .
git commit -m "Initial commit: ReceiptInfoExtractorAgent core engine and README"
git branch -M main
git remote add origin https://github.com/RealGobz/ReceiptInfoExtractorAgent.git
git push -u origin main
```

---

## 📄 License

This project is licensed under the MIT License.