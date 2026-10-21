"""AI CSV Analyzer - Core Analysis Engine.

This module provides data extraction, descriptive statistics, missing value detection,
and Google Gemini AI insights for CSV datasets. It can be run as a standalone CLI tool
or imported as the analytics backend for the web interface.
"""

import csv
import io
import os
import sys
from collections import Counter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Keywords used to heuristically identify revenue/sales/amount columns (ordered by priority)
SALES_KEYWORDS = [
    "revenue", "sales", "amount", "total", "price",
    "tutar", "satis", "satış", "gelir", "income"
]


# -----------------------------------------------------------------------------
# CSV Parsing & Ingestion
# -----------------------------------------------------------------------------

def parse_csv_rows(rows):
    """Separate header and data rows from raw row list."""
    if not rows:
        raise ValueError("CSV file is empty.")
    return rows[0], rows[1:]


def read_csv(file_path):
    """Read a CSV file from disk safely handling UTF-8 and BOM encodings."""
    try:
        # utf-8-sig automatically strips Excel's UTF-8 BOM character if present
        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        raise SystemExit(f"Error: File '{file_path}' not found. Please check the path.")
    except UnicodeDecodeError:
        raise SystemExit("Error: File could not be decoded as UTF-8. Please verify encoding.")
    except (csv.Error, OSError) as e:
        raise SystemExit(f"Error reading CSV file: {e}")

    return parse_csv_rows(rows)


def parse_csv_stream(stream):
    """Parse CSV data from an in-memory text stream or file-like object."""
    try:
        reader = csv.reader(stream)
        rows = list(reader)
    except Exception as e:
        raise ValueError(f"Unable to parse CSV content: {e}")
    return parse_csv_rows(rows)


# -----------------------------------------------------------------------------
# Data Extraction Helpers
# -----------------------------------------------------------------------------

def get_column_values(data_rows, col_index):
    """Extract non-empty string values for a specific column index."""
    values = []
    for row in data_rows:
        if col_index < len(row):
            cell = row[col_index].strip()
            if cell != "":
                values.append(cell)
    return values


def to_float(value_str):
    """Convert string to float supporting both '.' and ',' decimal separators."""
    try:
        return float(value_str.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def get_numeric_column_values(data_rows, col_index):
    """Return list of floats if a column is strictly numeric, otherwise None."""
    raw_values = get_column_values(data_rows, col_index)
    if not raw_values:
        return None

    numbers = []
    for val in raw_values:
        num = to_float(val)
        if num is None:
            return None
        numbers.append(num)
    return numbers


# -----------------------------------------------------------------------------
# Statistical & Categorical Analysis
# -----------------------------------------------------------------------------

def count_missing(columns, data_rows):
    """Calculate missing value counts and percentages for each column."""
    total = len(data_rows)
    result = {}
    for i, col in enumerate(columns):
        present_count = len(get_column_values(data_rows, i))
        missing_count = total - present_count
        percent = (missing_count / total * 100) if total > 0 else 0.0
        result[col] = (missing_count, percent)
    return result


def compute_numeric_stats(columns, data_rows):
    """Compute total, mean, min, and max for each numeric column."""
    stats = {}
    for i, col in enumerate(columns):
        numbers = get_numeric_column_values(data_rows, i)
        if numbers is not None and len(numbers) > 0:
            stats[col] = {
                "total": sum(numbers),
                "average": sum(numbers) / len(numbers),
                "min": min(numbers),
                "max": max(numbers),
            }
    return stats


def detect_sales_column(numeric_stats_dict):
    """Heuristically identify the primary sales/revenue/amount column."""
    for keyword in SALES_KEYWORDS:
        for col_name in numeric_stats_dict:
            if keyword in col_name.lower():
                return col_name
    return None


def find_top_categories(columns, data_rows, limit=5):
    """Identify the top recurring values in text/categorical columns."""
    result = {}
    for i, col in enumerate(columns):
        values = get_column_values(data_rows, i)
        if not values or get_numeric_column_values(data_rows, i) is not None:
            continue
        counts = Counter(values)
        if counts and counts.most_common(1)[0][1] > 1:
            result[col] = counts.most_common(limit)
    return result


# -----------------------------------------------------------------------------
# Google Gemini AI Integration (Bilingual Support: TR & EN)
# -----------------------------------------------------------------------------

def prepare_ai_summary(columns, data_rows, stats, missing, sales_col, top_cats, lang="en"):
    """Format an optimized, compact statistical summary in the selected language."""
    if lang == "tr":
        lines = [
            f"Toplam Satır: {len(data_rows)}",
            f"Sütunlar: {', '.join(columns)}",
            "\nEksik Veriler:"
        ]
        has_missing = False
        for col, (count, pct) in missing.items():
            if count > 0:
                lines.append(f"  - {col}: {count} adet eksik (%{pct:.1f})")
                has_missing = True
        if not has_missing:
            lines.append("  - Hiçbir sütunda eksik veri yok.")

        lines.append("\nSayısal İstatistikler:")
        if stats:
            for col, s in stats.items():
                lines.append(
                    f"  - {col}: Toplam={s['total']:,.2f}, Ortalama={s['average']:,.2f}, "
                    f"Min={s['min']:,.2f}, Max={s['max']:,.2f}"
                )
        else:
            lines.append("  - Sayısal sütun bulunamadı.")

        if sales_col and sales_col in stats:
            s = stats[sales_col]
            lines.append(f"\nAlgılanan Satış/Gelir Sütunu ({sales_col}):")
            lines.append(f"  - Toplam Tutar: {s['total']:,.2f}")
            lines.append(f"  - İşlem Başına Ortalama: {s['average']:,.2f}")
            lines.append(f"  - En Yüksek İşlem: {s['max']:,.2f}")
            lines.append(f"  - En Düşük İşlem: {s['min']:,.2f}")

        lines.append("\nKategorik Dağılımlar (En Sık Geçen Değerler):")
        if top_cats:
            for col, items in top_cats.items():
                item_strs = [f"{val} ({cnt}x)" for val, cnt in items]
                lines.append(f"  - {col}: {', '.join(item_strs)}")
        else:
            lines.append("  - Belirgin kategorik metin bulunamadı.")

        lines.append("\nÖrnek Kayıtlar (İlk 3 Satır):")
        for row in data_rows[:3]:
            lines.append(f"  {row}")

        return "\n".join(lines)

    # Default: English
    lines = [
        f"Total Rows: {len(data_rows)}",
        f"Columns: {', '.join(columns)}",
        "\nMissing Values:"
    ]
    has_missing = False
    for col, (count, pct) in missing.items():
        if count > 0:
            lines.append(f"  - {col}: {count} missing ({pct:.1f}%)")
            has_missing = True
    if not has_missing:
        lines.append("  - No missing values detected.")

    lines.append("\nNumeric Column Statistics:")
    if stats:
        for col, s in stats.items():
            lines.append(
                f"  - {col}: Total={s['total']:,.2f}, Average={s['average']:,.2f}, "
                f"Min={s['min']:,.2f}, Max={s['max']:,.2f}"
            )
    else:
        lines.append("  - No numeric columns found.")

    if sales_col and sales_col in stats:
        s = stats[sales_col]
        lines.append(f"\nPrimary Financial/Sales Metric ({sales_col}):")
        lines.append(f"  - Total Volume/Revenue: {s['total']:,.2f}")
        lines.append(f"  - Transaction Average: {s['average']:,.2f}")
        lines.append(f"  - Highest Record: {s['max']:,.2f}")
        lines.append(f"  - Lowest Record: {s['min']:,.2f}")

    lines.append("\nCategorical Distributions (Top Recurring):")
    if top_cats:
        for col, items in top_cats.items():
            item_strs = [f"{val} ({cnt}x)" for val, cnt in items]
            lines.append(f"  - {col}: {', '.join(item_strs)}")
    else:
        lines.append("  - No recurring text categories identified.")

    lines.append("\nSample Records (First 3 Rows):")
    for row in data_rows[:3]:
        lines.append(f"  {row}")

    return "\n".join(lines)


def generate_ai_report(summary_text, lang="en"):
    """Send dataset summary to Google Gemini API and generate insights."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        if lang == "tr":
            warning = (
                "Bilgi: Google Gemini API anahtarı ayarlanmamış.\n"
                "AI analiz raporunu alabilmek için:\n"
                "  1. https://aistudio.google.com/ adresinden ücretsiz anahtar alın.\n"
                "  2. .env dosyasını açıp ekleyin: GEMINI_API_KEY=anahtarınız\n"
                "  3. Analizi tekrar çalıştırın."
            )
        else:
            warning = (
                "Notice: Google Gemini API key is not configured.\n"
                "To enable automated AI business intelligence reports:\n"
                "  1. Obtain a free API key from https://aistudio.google.com/\n"
                "  2. Add it to your .env file: GEMINI_API_KEY=your_key_here\n"
                "  3. Re-run analysis to generate insights."
            )
        return None, warning

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if lang == "tr":
        prompt = f"""Sen deneyimli bir kıdemli veri ve iş analistisin. Aşağıda bir CSV veri setinden Python ile çıkarılmış istatistiki özet ve örnek kayıtlar yer almaktadır.

KESİNLİKLE UYULMASI GEREKEN KURALLAR:
1. Yalnızca sağlanan verilere ve istatistiklere dayanarak analiz yap.
2. Veride yer almayan bilgileri (örneğin müşteri memnuniyeti, teslimat süreleri, kargo maliyetleri) KESİNLİKLE UYDURMA ve varsayım üretme.
3. Profesyonel, net, akıcı ve aksiyon odaklı bir Türkçe kullan.

VERİ SETİ ÖZETİ:
{summary_text}

Raporunu tam olarak aşağıdaki 5 ana başlık altında yapılandır:
1. Genel Özet
2. Önemli Bulgular ve Trendler
3. Veri Kalitesi ve Anomaliler (eksik veriler, uç değerler)
4. Gelir ve Performans İçgörüleri
5. Eyleme Dönüştürülebilir Öneriler
"""
    else:
        prompt = f"""You are an expert senior data and business analyst. Below is a structured statistical summary and sample records extracted from a CSV dataset by Python.

CRITICAL RULES:
1. Ground your analysis STRICTLY in the provided data and statistics.
2. DO NOT fabricate, hallucinate, or assume metrics not present in the dataset (e.g. customer satisfaction, delivery times, shipping costs, or competitor market trends).
3. Provide professional, actionable, and clear insights in English.

DATASET SUMMARY:
{summary_text}

Generate a concise, high-value business report structured under these exact 5 headings:
1. Executive Summary
2. Key Discoveries & Trends
3. Data Quality & Anomalies (missing values, skewed ranges)
4. Revenue & Performance Insights
5. Actionable Recommendations
"""

    try:
        # pyrefly: ignore [missing-import]
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        if response and response.text:
            return response.text.strip(), None
        return None, "Error: Empty response returned by Gemini API."
    except Exception as e:
        clean_err = str(e).replace(api_key, "***")
        error_msg = (
            f"Error: Gemini API request failed.\n"
            f"Details: {clean_err}\n"
            "Please verify your API key validity, quota limits, and network connection."
        )
        return None, error_msg


# -----------------------------------------------------------------------------
# Integrated Analysis Pipeline
# -----------------------------------------------------------------------------

def run_full_analysis(columns, data_rows, lang="en"):
    """Execute complete analysis pipeline and assemble structured results."""
    stats = compute_numeric_stats(columns, data_rows)
    missing = count_missing(columns, data_rows)
    sales_col = detect_sales_column(stats)
    top_cats = find_top_categories(columns, data_rows)

    summary_text = prepare_ai_summary(columns, data_rows, stats, missing, sales_col, top_cats, lang=lang)
    ai_report, ai_error = generate_ai_report(summary_text, lang=lang)

    missing_dict = {
        col: {"count": count, "percent": round(pct, 1)}
        for col, (count, pct) in missing.items()
    }
    total_missing = sum(item["count"] for item in missing_dict.values())

    sales_analysis = None
    if sales_col and sales_col in stats:
        s = stats[sales_col]
        sales_analysis = {
            "column": sales_col,
            "total": s["total"],
            "average": s["average"],
            "max": s["max"],
            "min": s["min"],
        }

    return {
        "total_rows": len(data_rows),
        "total_columns": len(columns),
        "columns": columns,
        "preview": data_rows[:5],
        "missing": missing_dict,
        "total_missing": total_missing,
        "numeric_stats": stats,
        "sales_analysis": sales_analysis,
        "top_values": top_cats,
        "ai_report": ai_report,
        "ai_error": ai_error,
        "lang": lang,
    }


def main():
    """CLI Entry Point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_sales.csv"
    columns, data_rows = read_csv(file_path)
    results = run_full_analysis(columns, data_rows, lang="en")
    print("\nTotal Rows:", results["total_rows"], "| Columns:", results["total_columns"])
    if results["ai_report"]:
        print("\n=== AI REPORT ===\n", results["ai_report"])


if __name__ == "__main__":
    main()
