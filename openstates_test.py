# import packages
import requests
import json
import sqlite3
import pdfplumber
import os

# set API key and headers
API_KEY = "4dca6d1d-5c67-4cc3-8c68-8ca754b4f158"
headers = {"X-API-KEY": API_KEY}

params = {
    "jurisdiction": "Maryland",
    "session": "2025",
    "per_page": 5, # for testing, just keep 5 bills
    "include": ["sponsorships", "documents"] # include both sponsorships and documents as a list
}

response = requests.get("https://v3.openstates.org/bills", headers=headers, params=params)
data = response.json()

print(json.dumps(data, indent=4))

# store extracted text for each bill
bill_texts = {}

for bill in data.get("results", []):
    identifier = bill.get("identifier")
    title = bill.get("title")
    print(f"Bill: {identifier} - {title}") 

    documents = bill.get("documents", [])
    bill_text = ""  # Initialize text for this bill
       
    sponsorships = bill.get("sponsorships", [])
    if sponsorships:
        print("  Sponsors:")
        for s in sponsorships:
            person = s.get("person", {})
            full_name = person.get("name", s.get("name", "Unknown"))
            role = s.get("classification", "sponsor")
            print(f"    - {full_name} [{role}]")
    else:
        print("  No sponsors found")

    if documents:
        print("  Documents:")
        for doc in documents:
            note = doc.get("note", "")
            links = doc.get("links", [])
            for link in links:
                doc_url = link.get("url")
                media_type = link.get("media_type", "")
                if doc_url and media_type == "application/pdf":
                    print(f"    - {note}: {doc_url}")
                    try:
                        r = requests.get(doc_url)
                        r.raise_for_status()  
                        # Create docs folder if it doesn't exist
                        os.makedirs("docs", exist_ok=True)
                        # Replace spaces and special characters in filename
                        safe_identifier = identifier.replace(" ", "_").replace("/", "_")
                        pdf_filename = f"docs/{safe_identifier}_{note.replace(' ', '_')}.pdf"
                        with open(pdf_filename, 'wb') as f:
                            f.write(r.content)
                        print(f"      Downloaded: {pdf_filename}")
                        
                        # Extract text
                        with pdfplumber.open(pdf_filename) as pdf:
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    bill_text += page_text + "\n"
                    except Exception as e:
                        print(f"      Error downloading/processing {doc_url}: {e}")
    else:
        print("  No documents found")
    
    # Store the extracted text for this bill
    bill_texts[identifier] = bill_text
    


conn = sqlite3.connect('bills.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT,
        title TEXT,
        sponsor TEXT,
        role TEXT,
        classification TEXT,
        full_name TEXT,
        text TEXT
    )
''')

# Insert the bill info into sqlite3 db 
for bill in data.get("results", []):
    identifier = bill.get("identifier")
    title = bill.get("title")
    bill_text = bill_texts.get(identifier, "")  # Get the extracted text 
    
    sponsorships = bill.get("sponsorships", [])
    if sponsorships:
        for s in sponsorships:
            person = s.get("person", {})
            full_name = person.get("name", s.get("name", "Unknown"))
            role = s.get("classification", "sponsor")
            
            cursor.execute('''
                INSERT INTO bills (identifier, title, sponsor, role, classification, full_name, text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (identifier, title, s.get("name", "Unknown"), role, s.get("classification", ""), full_name, bill_text))
    else:
        # Insert bill if no sponsor
        cursor.execute('''
            INSERT INTO bills (identifier, title, sponsor, role, classification, full_name, text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (identifier, title, None, None, None, None, bill_text))

conn.commit()
conn.close()

