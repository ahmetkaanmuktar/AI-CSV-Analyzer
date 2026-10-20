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
    """Separate header and data rows from raw row list.

    Args:
        rows (list): List of row lists extracted from a CSV.

    Returns:
        tuple: (column_names, data_rows)

    Raises:
        ValueError: If the CSV contains no rows.
    """
    if not rows:
        raise ValueError("CSV file is empty.")
    return rows[0], rows[1:]


def read_csv(file_path):
    """Read a CSV file from disk safely handling UTF-8 and BOM encodings.

    Args:
        file_path (str): Path to target CSV file.

    Returns:
        tuple: (column_names, data_rows)
    """
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
    """Parse CSV data from an in-memory text stream or file-like object.

    Args:
        stream (io.StringIO): Open text stream.

    Returns:
        tuple: (column_names, data_rows)
    """
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
    """Extract non-empty string values for a specific column index.

    Args:
        data_rows (list): List of rows.
        col_index (int): Zero-based column index.

    Returns:
        list: Non-empty trimmed string values.
    """
    values = []
    for row in data_rows:
        if col_index < len(row):
            cell = row[col_index].strip()
            if cell != "":
                values.append(cell)
    return values


def to_float(value_str):
    """Convert string to float supporting both '.' and ',' decimal separators.

    Args:
        value_str (str): Input string.

    Returns:
        float or None: Parsed number or None if conversion fails.
    """
    try:
        return float(value_str.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def get_numeric_column_values(data_rows, col_index):
    """Return list of floats if a column is strictly numeric, otherwise None.

    Args:
        data_rows (list): List of rows.
        col_index (int): Zero-based column index.

    Returns:
        list of float or None: List of numbers if purely numeric, else None.
    """
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
    """Calculate missing value counts and percentages for each column.

    Args:
        columns (list): Column headers.
        data_rows (list): Data rows.

    Returns:
        dict: Mapping column -> (missing_count, percentage)
    """
    total = len(data_rows)
    result = {}
    for i, col in enumerate(columns):
        present_count = len(get_column_values(data_rows, i))
        missing_count = total - present_count
        percent = (missing_count / total * 100) if total > 0 else 0.0
        result[col] = (missing_count, percent)
    return result


def compute_numeric_stats(columns, data_rows):
    """Compute total, mean, min, and max for each numeric column.

    Args:
        columns (list): Column headers.
        data_rows (list): Data rows.

    Returns:
        dict: Mapping numeric column -> stats dict
    """
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
    """Heuristically identify the primary sales/revenue/amount column.

    Args:
        numeric_stats_dict (dict): Dictionary of computed numeric statistics.

    Returns:
        str or None: Detected column name or None.
    """
    for keyword in SALES_KEYWORDS:
        for col_name in numeric_stats_dict:
            if keyword in col_name.lower():
                return col_name
    return None


def find_top_categories(columns, data_rows, limit=5):
    """Identify the top recurring values in text/categorical columns.

    Args:
        columns (list): Column headers.
        data_rows (list): Data rows.
        limit (int): Maximum recurring items to return per column.

    Returns:
        dict: Mapping column -> list of (value, count) tuples
    """
    result = {}
    for i, col in enumerate(columns):
        values = get_column_values(data_rows, i)
        # Skip empty columns and numeric columns
        if not values or get_numeric_column_values(data_rows, i) is not None:
            continue
        counts = Counter(values)
        # Only include columns where at least one value repeats
        if counts and counts.most_common(1)[0][1] > 1:
            result[col] = counts.most_common(limit)
    return result


# -----------------------------------------------------------------------------
# Google Gemini AI Integration
# -----------------------------------------------------------------------------

def prepare_ai_summary(columns, data_rows, stats, missing, sales_col, top_cats):
    """Format an optimized, compact statistical summary to minimize API token cost.

    Args:
        columns (list): Column names.
        data_rows (list): Data rows.
        stats (dict): Numeric stats.
        missing (dict): Missing stats.
        sales_col (str or None): Sales column name.
        top_cats (dict): Categorical distributions.

    Returns:
        str: Concise text summary of dataset properties.
    """
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


def generate_ai_report(summary_text):
    """Send dataset summary to Google Gemini API and generate a business intelligence report.

    Args:
        summary_text (str): Condensed statistical summary.

    Returns:
        tuple: (report_text, error_message)
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    # Informative guidance if API key is unconfigured
    if not api_key or api_key == "your_gemini_api_key_here":
        warning = (
            "Notice: Google Gemini API key is not configured.\n"
            "To enable automated AI business intelligence reports:\n"
            "  1. Obtain a free API key from https://aistudio.google.com/\n"
            "  2. Add it to your .env file: GEMINI_API_KEY=your_key_here\n"
            "  3. Re-run analysis to generate insights."
        )
        return None, warning

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

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
        # Security: ensure API key is never exposed in error tracebacks
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

def run_full_analysis(columns, data_rows):
    """Execute complete analysis pipeline and assemble structured results for UI and API consumption.

    Args:
        columns (list): Column headers.
        data_rows (list): Data records.

    Returns:
        dict: Complete structured analysis payload.
    """
    stats = compute_numeric_stats(columns, data_rows)
    missing = count_missing(columns, data_rows)
    sales_col = detect_sales_column(stats)
    top_cats = find_top_categories(columns, data_rows)

    summary_text = prepare_ai_summary(columns, data_rows, stats, missing, sales_col, top_cats)
    ai_report, ai_error = generate_ai_report(summary_text)

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
    }


# -----------------------------------------------------------------------------
# CLI Presentation
# -----------------------------------------------------------------------------

def print_cli_report(columns, data_rows, results):
    """Print clean formatted report to terminal."""
    def header(title):
        print("\n" + "=" * 60)
        print(title)
        print("=" * 60)

    header("GENERAL OVERVIEW")
    print(f"Total Rows    : {len(data_rows)}")
    print(f"Total Columns : {len(columns)}")
    print(f"Columns       : {', '.join(columns)}")
    print("\nFirst 5 Records:")
    for row in data_rows[:5]:
        print("  ", row)

    header("MISSING VALUE REPORT")
    print(f"{'Column':<20}{'Missing':>8}{'Total Rows':>15}{'Percent':>10}")
    print("-" * 53)
    for col, item in results["missing"].items():
        print(f"{col:<20}{item['count']:>8}{len(data_rows):>15}{item['percent']:>9.1f}%")

    header("NUMERIC COLUMN STATISTICS")
    stats = results["numeric_stats"]
    if stats:
        print(f"{'Column':<15}{'Total':>14}{'Average':>14}{'Min':>12}{'Max':>12}")
        print("-" * 67)
        for col, s in stats.items():
            print(f"{col:<15}{s['total']:>14,.2f}{s['average']:>14,.2f}{s['min']:>12,.2f}{s['max']:>12,.2f}")
    else:
        print("No numeric columns detected.")

    header("SALES & REVENUE ANALYSIS")
    if results["sales_analysis"]:
        sa = results["sales_analysis"]
        print(f"Detected Column : {sa['column']}")
        print(f"Total Volume    : {sa['total']:,.2f}")
        print(f"Average Ticket  : {sa['average']:,.2f}")
        print(f"Maximum Ticket  : {sa['max']:,.2f}")
        print(f"Minimum Ticket  : {sa['min']:,.2f}")
    else:
        print("No specific sales/revenue column detected automatically.")

    header("TOP CATEGORIES (Up to 5)")
    tops = results["top_values"]
    if tops:
        for col, items in tops.items():
            print(f"\n{col}:")
            for val, cnt in items:
                print(f"  {val:<20} {cnt} times")
    else:
        print("No recurring categorical text found.")

    header("AI ANALYSIS REPORT")
    if results["ai_report"]:
        print(results["ai_report"])
    elif results["ai_error"]:
        print(results["ai_error"])


def main():
    """CLI Entry Point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_sales.csv"
    columns, data_rows = read_csv(file_path)
    results = run_full_analysis(columns, data_rows)
    print_cli_report(columns, data_rows, results)


if __name__ == "__main__":
    main()
