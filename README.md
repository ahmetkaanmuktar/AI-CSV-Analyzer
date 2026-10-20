# AI CSV Analyzer

> An intelligent, production-ready data analysis tool that ingests CSV datasets, computes descriptive statistics in Python, and leverages the Google Gemini API to generate executive business intelligence reports.

---

## 📌 Project Overview

**AI CSV Analyzer** is designed for professionals, analysts, and business owners who need immediate insights from structured tabular data without tedious manual spreadsheet operations.

Instead of naively uploading massive raw CSV datasets to an LLM—which burns tokens and causes context-window bloat—AI CSV Analyzer employs a **smart two-tier architecture**:
1. **Deterministic Python Core:** Calculates descriptive statistics, missing value ratios, numeric aggregates, and categorical frequencies locally with zero token cost.
2. **Generative AI Layer:** Sends a concise, privacy-conscious statistical summary to the Google Gemini API to produce grounded, hallucination-free executive business recommendations.

---

## ✨ Features

- **Automated Ingestion & Parsing:** Safely parses standard and Excel-exported CSV files (supporting UTF-8 BOM encoding).
- **Descriptive Statistics:** Automatically identifies numeric columns and calculates totals, averages, minimums, and maximums.
- **Data Quality & Hygiene Audit:** Reports exact missing value counts and percentage emptiness with visual progress bars.
- **Smart Financial Metric Detection:** Automatically identifies revenue, sales, price, and amount columns to highlight key top-line business indicators.
- **Categorical Frequency Breakdown:** Pinpoints the top recurring categories in text columns (e.g., product lines, regions, customer segments).
- **Grounded AI Business Intelligence:** Prompts Google Gemini with strict guardrails to prevent hallucinations and deliver insights under 5 structured headers:
  1. Executive Summary
  2. Key Discoveries & Trends
  3. Data Quality & Anomalies
  4. Revenue & Performance Insights
  5. Actionable Recommendations
- **Modern Responsive Web UI:** Built with vanilla HTML5, CSS3, and modern JavaScript. Features drag-and-drop file upload, instant sample demonstration, mobile responsiveness, and clean dark-mode aesthetics.
- **Zero Disk Footprint:** Uploaded files are processed strictly in-memory (`io.StringIO`) and never stored permanently on disk.
- **CLI & Web Dual Support:** Run the full analysis directly in your terminal or launch the interactive browser dashboard.

---

## 🛠️ Technologies

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3.8+ / Flask | Lightweight, robust web server and in-memory data processing |
| **Core Analytics** | Python Standard Library | `csv`, `collections.Counter`, `io` (fast, dependency-free) |
| **Generative AI** | Google GenAI SDK (`google-genai`) | Official modern SDK for Google Gemini models |
| **Config & Secrets**| `python-dotenv` | Clean, twelve-factor app environment configuration |
| **Frontend** | Vanilla HTML5 / CSS3 / ES6 JS | Fast, zero-framework, fully responsive interface |

---

## 🔄 How It Works

The data processing pipeline follows a cost-optimized, secure architecture:

```
┌─────────────────┐
│   CSV Upload    │  (Drag & drop or CLI file path)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Python Core   │  • Parses rows & headers
│  Data Analysis  │  • Computes numeric stats (sum, avg, min, max)
│                 │  • Audits missing values & top categories
└────────┬────────┘
         │
         ▼ (Compact statistical summary, minimal token usage)
┌─────────────────┐
│   Gemini API    │  • Strict prompt with anti-hallucination guardrails
│   Processing    │  • Evaluates business implications
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    AI Report    │  • 5 structured analytical sections
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Web Interface  │  • Interactive metric cards, tables, and AI report
└─────────────────┘
```

---

## 📋 Project Structure

```
AI-CSV-Analyzer/
├── app.py                # Flask web server and API endpoints
├── main.py               # Core Python analytics engine & standalone CLI interface
├── templates/
│   └── index.html        # Modern dashboard template
├── static/
│   ├── style.css         # Responsive styling, tables, and dark theme
│   └── script.js         # Client-side validation, drag-and-drop, and UI updates
├── sample_sales.csv      # Ready-to-use demonstration dataset
├── requirements.txt      # Production dependencies
├── .env                  # Local secrets (ignored by Git)
├── .env.example          # Safe template for environment variables
├── .gitignore            # Git exclusion rules
└── README.md             # Project documentation
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/AI-CSV-Analyzer.git
cd AI-CSV-Analyzer
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

1. Copy `.env.example` to create your local `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and configure your API key:
   ```env
   # Obtain a free API key at https://aistudio.google.com/
   GEMINI_API_KEY=AIzaSy...your_actual_key_here

   # Desired Gemini model (default: gemini-2.5-flash)
   GEMINI_MODEL=gemini-2.5-flash
   ```

> ℹ️ **Note:** If no API key is configured, the application will still compute and display all Python statistical metrics and provide on-screen guidance on how to enable AI reports.

---

## 💻 How to Run

### Option A: Launch the Web Application
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

- Click **"Choose CSV File"** or drag-and-drop your dataset.
- Or click **"Quick Demo with Sample"** to instantly test with the bundled dataset.

### Option B: Run via Terminal (CLI Mode)
```bash
# Analyze bundled demo dataset
python main.py

# Or analyze any custom CSV
python main.py path/to/your_data.csv
```

---

## 📊 Example Usage & Output

When analyzing `sample_sales.csv`:

- **Total Records:** 16 Rows, 7 Columns
- **Financial Metric:** Revenue detected with `Total = 108,610.00`, `Average = 7,757.86`, `Max = 30,000.00`
- **Data Hygiene:** 4 missing cells identified and mapped with percentage indicators
- **Gemini AI Report:** Provides an Executive Summary highlighting top-selling categories (Electronics), revenue distribution across cities (Istanbul, Ankara, Izmir), and recommendations on inventory balancing.

---

## 🔒 Security & Privacy Notes

- **Secret Isolation:** API keys are loaded via `python-dotenv` and strictly isolated to server memory. They are **never** exposed in frontend HTML, client-side scripts, or error messages.
- **Git Protection:** The `.gitignore` file strictly blocks `.env`, local environment variables, cache files, and virtual environments from ever being committed.
- **In-Memory Ingestion:** User files are processed in RAM streams (`io.StringIO`) and immediately discarded after analysis. No customer data is written to disk or databases.
- **Upload Limit:** Enforces a 16 MB request limit (`MAX_CONTENT_LENGTH`) to protect server resources against denial-of-service attempts.

---

## 🔮 Future Improvements

- [ ] Export reports directly to formatted PDF or Markdown summaries.
- [ ] Interactive "Chat with your CSV" conversational assistant widget.
- [ ] Automated chart generation (bar and line plots via Chart.js).
- [ ] Support for Excel (`.xlsx`) and JSON files.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
