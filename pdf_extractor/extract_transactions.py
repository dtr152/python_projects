 
#Script: extract_transactions.py
#A python script for the purpose of extracting transaction history from pdf bank statements
#Author: David Redmond

import pdfplumber
import os
import re
import csv
from datetime import datetime

print ("Welcome to the PDF Transaction Editor")

output_rows = [] #store all valid transaction rows here
headers = None

#prompt user to input file path/name
pdf_path = input("Enter the full path to your bank statement: "). strip()

if not os.path.isfile(pdf_path):
    print("❌ File not found. Please check the path.")
    exit(1)

print("✅ PDF file found. We'll start processing it...")

#Function to filter only transaction rows
def is_transaction_row(row):
    """Returns True if the row appears to be a transaction based on:
       - Not being a header
       - Contains a partial or full date string
       - Contains a valid comment
       """
    
    if not cleaned_row or len(cleaned_row) < 4:
        return False
    
    cleaned = [cell.replace("\n", " ").strip() if cell else "" for cell in row]

   
    
    #look for a date-like value (relaxed YYYY-MM or YYYY-MM-DD-ish)
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{1,2}')
    has_date = any(date_pattern.search(cell.replace(" ", "")) for cell in cleaned_row)

    #look for a valid amount (e.g. -7.09 or 123.45)
    amount_pattern = re.compile(r'^-?\d+(\.\d+)?$')
    has_amount = any(amount_pattern.match(cell.replace("€", "").replace(",","").strip()) for cell in cleaned_row)

    return has_date and has_amount    


    # Match format like 2025-07-25
    date_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')

    for cell in cleaned_row:
        if date_pattern.search(cell):
            return True
    
    return False



#open pdf, loop through pages, find and print data
with pdfplumber.open(pdf_path) as pdf:
    print(f"📄 PDF has {len(pdf.pages)} pages.")

    for page_num, page in enumerate(pdf.pages, start=1):
        print(f"\n 🔎 Page {page_num}")
        tables = page.extract_tables()

        for table_index, table in enumerate(tables):
            print(f" Table {table_index + 1} has {len(table)} rows.")


            for row in table:
                #clean up the row: remove line breaks and extra spaces
                cleaned_row = [cell.replace("\n", " ").strip() if cell else "" for cell in row]

                #Detect headers if not already set
                if headers is None:
                    if any("date" in col.lower() for col in cleaned_row if col):
                        headers = cleaned_row
                    print(f"✅ Detected headers: {headers}")
                    continue #skip header

                #skip duplicate header rows
                if headers and cleaned_row == headers:
                    continue

                if is_transaction_row(cleaned_row):
                    output_rows.append(cleaned_row) #Save valid rows

                else:
                    print( "   ❌ (ignored)", cleaned_row)

#Fallback headers if not found
if not headers:
    headers = [f"Column {i+1}" for i in range(max(len(r) for r in output_rows))]


# ✅ Write to CSV with headers
with open("extracted_transactions.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)
    writer.writerows(output_rows)

print("✅ CSV file with headers written: extracted_transactions.csv")