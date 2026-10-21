# 📊 AI-Powered Expense Audit & Analytics Platform

A dynamic financial intelligence dashboard built with Streamlit. This platform provides real-time spend analytics, multi-channel data ingestion (SMS, bank statement PDFs, manual entry), dual-layer synchronization with a Pinecone vector database for AI-assisted natural language querying, and an enterprise-grade 3-tier Data Governance & Audit Lifecycle Management suite.

---

## 🌟 Key Features

* **📈 Dynamic Financial Analytics:** Automatic calculation of consolidated spending, total transaction metrics, dynamic gradient category cards, and segment share breakdowns.
* **📥 Multi-Channel Data Ingestion:**
  * **Manual Entry:** Quick logging with automated expense category recommendations.
  * **Batch SMS Parser:** Extract structured financial transactions directly from raw SMS text logs using RegEx pattern matching.
  * **Document Reader:** Parse bank statement PDFs and images (`pypdf`), extracting transaction amounts and dates automatically.
* **🤖 Conversational AI Assistant:** Pinecone vector database integration paired with interactive quick-action prompt pills for intelligent natural language ledger querying.
* **🛡️ Data Governance & Audit Suite (3-Level Cleanup):**
  * **Level 1 (Item-Level):** Multi-select individual or batch transaction row deletion.
  * **Level 2 (Category-Level):** Complete purge of specific segment categories and associated expense rows (e.g., removing legacy segments like "Loans & Debt").
  * **Level 3 (Global Reset):** Wipes transaction history clean across both local storage and vector DB while preserving segment categories.
* **⚡ Dual-Layer Sync & Safeguards:** Maintains 100% data consistency across local CSV ledgers (`master_ledger.csv`) and remote Pinecone vector memory, complete with confirmation safeguards to prevent accidental data loss.

## 🚀 Getting Started**
### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Clone the Repository
Bash
git clone [https://github.com/Daniel3864/AI-Powered-Expense-Audit-Analytics-Platform.git](https://github.com/Daniel3864/AI-Powered-Expense-Audit-Analytics-Platform.git)
cd AI-Powered-Expense-Audit-Analytics-Platform
### 3. Set Up a Virtual Environment (Recommended)
Bash
 macOS/Linux
python3 -m venv venv
source venv/bin/activate

 Windows
python -m venv venv
venv\Scripts\activate
### 4. Install Dependencies
Bash
pip install -r requirements.txt
### 5. Configure API Secrets
Create a .streamlit/secrets.toml file in the root directory to store your credentials securely:

Ini, TOML
PINECONE_API_KEY = "your-pinecone-api-key"
PINECONE_ENVIRONMENT = "your-pinecone-environment"
PINECONE_INDEX_NAME = "expense-audit"

### 6. Run the Application
Bash
#### streamlit run app.py
Open your browser and navigate to http://localhost:8501.

## 🛡️ Data Governance & Compliance
The platform follows strict Dual-Layer Synchronization principles:

Local State & Storage Layer: Transactions are recorded and stored in Pandas DataFrames and exported to master_ledger.csv.

Vector Memory Layer: Textual representations of transactions are embedded and stored in Pinecone for semantic search.

Executing any Level 1, Level 2, or Level 3 delete action automatically synchronizes both layers, ensuring the AI Assistant never cites purged data.

## 🛠️ Tech Stack
### Frontend & Dashboard: Streamlit

### Data Processing: Pandas, NumPy

### PDF Parsing: PyPDF

### Vector Database: Pinecone


---

## 📁 Project Architecture

```text
.
├── app.py                      # Main application entry point / Overview dashboard
├── pages/
│   ├── 1_Segment_Analytics.py   # In-depth segment-wise expenditure analysis
│   ├── 2_Data_Ingestion.py      # Manual, SMS, PDF input & Data Governance Suite
│   └── 4_Assistant.py           # AI Chatbot Assistant & vector query interface
├── utils/
│   ├── state_manager.py         # App state management & master ledger persistence
│   ├── categorizer.py           # Smart category classification logic
│   └── vector_helper.py         # Pinecone vector embeddings & sync pipeline
├── master_ledger.csv            # Local transaction database (ignored by git)
├── requirements.txt             # Project Python dependencies
└── README.md                    # Project documentation


Language: Python 3.9+
