# Script: extract_transactions.py
# A python script for extracting transaction history from PDF bank statements
# Author: David Redmond

import PyPDF2
import pdfplumber
import os
import re
import csv
import getpass
from datetime import datetime

print("Welcome to the PDF Transaction Editor")

pdf = None
output_rows = []
headers = None

def is_transaction_row(row):
    """Returns True if the row appears to be a transaction based on:
       - Contains a date-like string (year or 8-digit date)
       - Contains a valid amount (number with optional commas/decimals)
    """
    if not row or len(row) < 2:
        return False

    cleaned = [cell.replace("\n", " ").strip() if cell else "" for cell in row]

    # Relaxed date pattern: matches YYYY, YYYYMMDD, or DDMMYYYY, or YYYY-MM-DD, or YYYY/MM/DD
    date_pattern = re.compile(
        r'(\d{4}[-/]\d{2}[-/]\d{2})|(\d{8})|(\d{4})'
    )
    has_date = any(date_pattern.search(cell) for cell in cleaned)

    # Relaxed amount pattern: matches numbers with optional commas and decimals
    amount_pattern = re.compile(r'-?\d[\d,]*\.?\d*')
    has_amount = any(amount_pattern.search(cell.replace("€", "").replace("$", "").replace(",", "").strip()) for cell in cleaned)

    return has_date and has_amount



def extract_date_from_row(row):
    """Finds the column that contains only a date and returns its index, else None."""
    date_pattern = re.compile(r'^(\d{4}[-/]\d{2}[-/]\d{2}|\d{8}|\d{4})$')
    for idx, cell in enumerate(row):
        if date_pattern.match(cell.strip()):
            return idx
    return None



# If headers exist, try to find the 'description' and 'date' columns
if headers:
    desc_idx = next((i for i, h in enumerate(headers) if 'description' in h.lower()), None)
    date_idx = next((i for i, h in enumerate(headers) if 'date' in h.lower()), None)

    for row in output_rows:
        # If description column contains a date, and there is a dedicated date column, remove date from description
        if desc_idx is not None and date_idx is not None:
            desc_cell = row[desc_idx]
            date_cell = row[date_idx]
            # Remove date from description if present
            date_in_desc_pattern = re.compile(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{8}|\d{4})')
            row[desc_idx] = date_in_desc_pattern.sub('', desc_cell).strip()
        else:
            # Fallback: try to find a column with only a date
            only_date_idx = extract_date_from_row(row)
                # Remove date from other columns
            for i, cell in enumerate(row):
                    if i != only_date_idx:
                        row[i] = re.sub(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{8}|\d{4})', '', cell).strip()






# Prompt user to input file path/name
pdf_path = input("Enter the full path to your bank statement: ").strip()

if not os.path.isfile(pdf_path):
    print("❌ File not found. Please check the path.")
    exit(1)

# Try to decrypt with PyPDF2 first
with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    if reader.is_encrypted:
        print("🔒 PDF is encrypted.")
        password = input("🔒 Please enter the PDF password: ")
        if reader.decrypt(password):
            print("✅ Decryption successful!")
            # Write decrypted PDF to memory
            from io import BytesIO
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            decrypted_stream = BytesIO()
            writer.write(decrypted_stream)
            decrypted_stream.seek(0)
            pdf_file_for_plumber = decrypted_stream
        else:
            print("❌ Decryption failed. Exiting.")
            exit(1)
    else:
        print("🔓 PDF is not encrypted.")
        f.seek(0)
        pdf_file_for_plumber = f

    # Use pdfplumber on the (possibly decrypted) PDF
    with pdfplumber.open(pdf_file_for_plumber) as pdf:
        print(f"📄 PDF has {len(pdf.pages)} pages.")

        for page_num, page in enumerate(pdf.pages, start=1):
            print(f"\n 🔎 Page {page_num}")
            tables = page.extract_tables()

            for table_index, table in enumerate(tables):
                print(f" Table {table_index + 1} has {len(table)} rows.")

                for row in table:
                    # Clean up the row: remove line breaks and extra spaces
                    cleaned_row = [cell.replace("\n", " ").strip() if cell else "" for cell in row]

                    # Detect headers if not already set
                    if headers is None:
                        if any("date" in col.lower() for col in cleaned_row if col):
                            headers = cleaned_row
                            print(f"✅ Detected headers: {headers}")
                            continue  # Skip header

                    # Skip duplicate header rows
                    if headers and cleaned_row == headers:
                        continue

                    if is_transaction_row(cleaned_row):
                        output_rows.append(cleaned_row)  # Save valid rows
                    else:
                        print("   ❌ (ignored)", cleaned_row)

if not output_rows:
    print("❌ No transactions were found in the PDF.")
    exit(1)

# Fallback headers if not found
if not headers:
    headers = [f"Column {i+1}" for i in range(max(len(r) for r in output_rows))]

# ✅ Write to CSV with headers
with open("extracted_transactions.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    writer.writerows(output_rows)

print("✅ CSV file with headers written: extracted_transactions.csv")

# Post-process output_rows to ensure date is extracted from the correct column
