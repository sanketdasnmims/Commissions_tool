# Commissions Tool

A suite of Python Flask web applications for SAP Commissions requirements management and document analysis.

---

## About

This project was built to streamline the process of capturing, structuring, and validating requirements for SAP Commissions implementations.

SAP Commissions projects are complex — they span multiple technical components (Workflow, ICM Engine, BTP/EDL, Embedded Analytics, Integrations) and typically require large volumes of structured requirements and test cases to go live. Writing these manually is time-consuming and error-prone.

This toolset uses the Anthropic Claude AI API to:

- **Extract** requirement candidates from raw source documents (PDFs, meeting notes, spec sheets)
- **Compose** structured, approval-ready requirements mapped to the correct SAP Commissions component
- **Generate** test cases automatically once a requirement is approved — with a hard gate preventing test generation on unapproved requirements
- **Identify and analyse** uploaded financial and business documents using AI

The project also includes a `CommSpec_Blueprint.md` that outlines the full production-grade architecture for scaling this into an enterprise tool — including a Next.js frontend, FastAPI backend, PostgreSQL database with vector search, and async background processing.

---

## Applications

| File | Description | Port |
|------|-------------|------|
| `Commission.py` | SAP Commissions Requirements & Test Creation Tool | 5002 |
| `Document_Identification.py` | AI-powered document identification and analysis | 5001 |
| `Application_test.py` | Household chore management web app | 5000 |

---

## Prerequisites

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/sanketdasnmims/Commissions_tool.git
cd Commissions_tool
```

### 2. Create and activate a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

> Never commit your `.env` file. It is already listed in `.gitignore`.

---

## Running the Applications

### SAP Commissions Requirements & Test Creation Tool

```bash
venv\Scripts\python Commission.py
```

Open: [http://localhost:5002](http://localhost:5002)

**Workflow:**
1. Upload a source document (PDF, TXT) or paste text describing a commission requirement
2. AI extracts requirement candidates using SAP Commissions domain knowledge
3. AI composes a structured, approval-ready requirement
4. Review and **Approve** or **Reject** the requirement
5. On approval, AI generates test cases (blocked until approved)
6. Export test cases as JSON

**Supported SAP Commissions components:** Workflow, BTP/EDL, ICM Engine, Embedded Analytics, Integration, Participants, Credit & Incentive, Batch Scheduling, Security

---

### Document Identification App

```bash
venv\Scripts\python Document_Identification.py
```

Open: [http://localhost:5001](http://localhost:5001)

**Features:**
- Upload PDF, PNG, JPG, WEBP, TXT, or CSV files
- AI identifies document type (Invoice, Balance Sheet, Bank Statement, etc.)
- Chat with the document
- Keyword-based classification rules
- Full-text search within documents
- Download uploaded files

---

### Chore Management App

```bash
venv\Scripts\python Application_test.py
```

Open: [http://localhost:5000](http://localhost:5000)

---

## Project Structure

```
Commissions_tool/
├── Commission.py              # SAP Commissions requirements & test tool
├── Document_Identification.py # Document analysis app
├── Application_test.py        # Chore management app
├── CommSpec_Blueprint.md      # Full architecture blueprint for Commission tool
├── requirements.txt           # Python dependencies
├── templates/                 # HTML templates
├── static/                    # CSS and JS assets
├── uploads/                   # Uploaded files (gitignored)
└── .env                       # API keys (gitignored — create this yourself)
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| anthropic | Claude AI API client |
| pdfplumber | PDF text extraction |
| python-dotenv | Load environment variables from `.env` |
| Flask-SQLAlchemy | Database ORM (chore app) |

---

## Notes

- `Commission.py` is a single-file prototype. All state is stored in memory per browser session — restarting the server clears all data. For a production-grade version, see `CommSpec_Blueprint.md`.
- `Document_Identification.py` persists document state to `doc_store.json` and saves uploaded files to the `uploads/` folder — both are gitignored.
