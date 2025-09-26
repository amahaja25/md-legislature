# import packages
import requests
import json
import sqlite3
import pdfplumber
import os
import time

# set API key and headers
API_KEY = "3f782772-bf3c-4873-80eb-1d011e3a8f83"
headers = {"X-API-KEY": API_KEY}

params = {
    "jurisdiction": "Maryland",
    "session": "2025",
    "per_page": 20,    # Maximum allowed by API
    "include": ["sponsorships", "documents"]  # API accepts list for multiple includes
}

# Fetch multiple pages
all_bills = []
bill_texts = {}

max_page = None
page = 1
while True:
    params["page"] = page
    print(f"\n=== Fetching page {page} ===")
    
    try:
        response = requests.get("https://v3.openstates.org/bills", headers=headers, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:  # Rate limit exceeded
            print(f"Rate limit exceeded on page {page}. Waiting 60 seconds...")
            time.sleep(60)  # Wait 60 seconds before retrying
            try:
                print(f"Retrying page {page}...")
                response = requests.get("https://v3.openstates.org/bills", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            except Exception as retry_e:
                print(f"Retry failed for page {page}: {retry_e}")
                break
        else:
            print(f"HTTP error fetching page {page}: {e}")
            break
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        break
    
    # Get pagination info from first response
    if page == 1:
        pagination = data.get("pagination", {})
        max_page = pagination.get("max_page", 1)
        total_items = pagination.get("total_items", 0)
        print(f"Total items available: {total_items}")
        print(f"Total pages available: {max_page}")
        per_page = pagination.get("per_page", 20)
        print(f"Items per page: {per_page}")
    
    # Add bills from this page
    results = data.get("results", [])
    print(f"Page {page}: {len(results)} bills fetched")
    all_bills.extend(results)
    
    # Break if no more results or we've reached the last page
    if not results:
        print(f"Breaking: No more results on page {page}")
        break
    if page >= max_page:
        print(f"Breaking: Reached max_page {max_page} on page {page}")
        break
    
    print(f"Continuing to page {page + 1}...")
    page += 1
    
    # Add a small delay to avoid rate limiting
    time.sleep(1)  # Wait 1 second between requests

print(f"Total bills fetched: {len(all_bills)}")
print(f"Pages processed: {page}")

# store extracted text for each bill
for bill in all_bills:
    identifier = bill.get("identifier")
    title = bill.get("title")
    chamber = bill.get("from_organization", {}).get("name", "unknown").capitalize()
    first_action_date = bill.get("first_action_date", "unknown")
    latest_action_date = bill.get("latest_action_date", "unknown")
    latest_action_description = bill.get("latest_action_description", "unknown")
    print(f"{chamber} Bill: {identifier} - {title}") 

    documents = bill.get("documents", [])
    bill_text = ""  # Initialize text for this bill
       
    sponsorships = bill.get("sponsorships", [])
    if sponsorships:
        print("  Sponsors:")
        for s in sponsorships:
            person = s.get("person", {})
            full_name = person.get("name", s.get("name", "Unknown"))
            party = person.get("party", "N/A")
            role = s.get("classification", "sponsor")
            district = person.get("current_role", {}).get("district", "N/A")

            print(f"    - {full_name} [{role}] (District: {district})")
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
                        # Create docs folder 
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


    
# connect to sqlite3 db
conn = sqlite3.connect('bills.db')
cursor = conn.cursor()

# Create table only if it doesn't exist (don't drop existing data)
# cursor.execute('DROP TABLE IF EXISTS bills')


# limit to 20 sponsors per bill (in the sample of ten, one bill has 18 sponsors and another had 16)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identifier TEXT UNIQUE,
        title TEXT,
        text TEXT,
        chamber TEXT,
        first_action_date TEXT,
        latest_action_date TEXT,
        latest_action_description TEXT,
        sponsor_1_name TEXT, sponsor_1_role TEXT, sponsor_1_party TEXT, sponsor_1_district TEXT,
        sponsor_2_name TEXT, sponsor_2_role TEXT, sponsor_2_party TEXT, sponsor_2_district TEXT,
        sponsor_3_name TEXT, sponsor_3_role TEXT, sponsor_3_party TEXT, sponsor_3_district TEXT,
        sponsor_4_name TEXT, sponsor_4_role TEXT, sponsor_4_party TEXT, sponsor_4_district TEXT,
        sponsor_5_name TEXT, sponsor_5_role TEXT, sponsor_5_party TEXT, sponsor_5_district TEXT,
        sponsor_6_name TEXT, sponsor_6_role TEXT, sponsor_6_party TEXT, sponsor_6_district TEXT,
        sponsor_7_name TEXT, sponsor_7_role TEXT, sponsor_7_party TEXT, sponsor_7_district TEXT,
        sponsor_8_name TEXT, sponsor_8_role TEXT, sponsor_8_party TEXT, sponsor_8_district TEXT,
        sponsor_9_name TEXT, sponsor_9_role TEXT, sponsor_9_party TEXT, sponsor_9_district TEXT,
        sponsor_10_name TEXT, sponsor_10_role TEXT, sponsor_10_party TEXT, sponsor_10_district TEXT,
        sponsor_11_name TEXT, sponsor_11_role TEXT, sponsor_11_party TEXT, sponsor_11_district TEXT,
        sponsor_12_name TEXT, sponsor_12_role TEXT, sponsor_12_party TEXT, sponsor_12_district TEXT,
        sponsor_13_name TEXT, sponsor_13_role TEXT, sponsor_13_party TEXT, sponsor_13_district TEXT,
        sponsor_14_name TEXT, sponsor_14_role TEXT, sponsor_14_party TEXT, sponsor_14_district TEXT,
        sponsor_15_name TEXT, sponsor_15_role TEXT, sponsor_15_party TEXT, sponsor_15_district TEXT,
        sponsor_16_name TEXT, sponsor_16_role TEXT, sponsor_16_party TEXT, sponsor_16_district TEXT,
        sponsor_17_name TEXT, sponsor_17_role TEXT, sponsor_17_party TEXT, sponsor_17_district TEXT,
        sponsor_18_name TEXT, sponsor_18_role TEXT, sponsor_18_party TEXT, sponsor_18_district TEXT,
        sponsor_19_name TEXT, sponsor_19_role TEXT, sponsor_19_party TEXT, sponsor_19_district TEXT,
        sponsor_20_name TEXT, sponsor_20_role TEXT, sponsor_20_party TEXT, sponsor_20_district TEXT,
        total_sponsors INTEGER
    )
''')

# Insert the bill info into sqlite3 db 
for bill in all_bills:
    identifier = bill.get("identifier")
    title = bill.get("title")
    bill_text = bill_texts.get(identifier, "") 
    chamber = bill.get("from_organization", {}).get("name", "unknown").capitalize()
    first_action_date = bill.get("first_action_date", "unknown")
    latest_action_date = bill.get("latest_action_date", "unknown")
    latest_action_description = bill.get("latest_action_description", "unknown")
     # Get extracted text 
    
    sponsorships = bill.get("sponsorships", [])
    
    # Prepare sponsor data
    sponsor_data = {}
    total_sponsors = len(sponsorships)
    
    for i, s in enumerate(sponsorships[:20]):  # Limit to 20 sponsors max
        person = s.get("person", {})
        full_name = person.get("name", s.get("name", "Unknown"))
        role = s.get("classification", "sponsor")
        
       # party and district
        party = person.get("party", "Unknown") if person else "Unknown"
        current_role = person.get("current_role", {}) if person else {}
        district = current_role.get("district", "Unknown") if current_role else "Unknown"
        
        sponsor_data[f'sponsor_{i+1}_name'] = full_name
        sponsor_data[f'sponsor_{i+1}_role'] = role
        sponsor_data[f'sponsor_{i+1}_party'] = party
        sponsor_data[f'sponsor_{i+1}_district'] = district
    
    # Fill in None for unused sponsor columns
    for i in range(len(sponsorships), 20):
        sponsor_data[f'sponsor_{i+1}_name'] = None
        sponsor_data[f'sponsor_{i+1}_role'] = None
        sponsor_data[f'sponsor_{i+1}_party'] = None
        sponsor_data[f'sponsor_{i+1}_district'] = None
    
    # Check if bill already exists
    cursor.execute('SELECT COUNT(*) FROM bills WHERE identifier = ?', (identifier,))
    if cursor.fetchone()[0] == 0:
        # Insert single row for this bill only if it doesn't exist
        cursor.execute('''
            INSERT INTO bills (
            identifier, title, text, chamber,
            first_action_date, latest_action_date, latest_action_description, total_sponsors,
            sponsor_1_name, sponsor_1_role, sponsor_1_party, sponsor_1_district,
            sponsor_2_name, sponsor_2_role, sponsor_2_party, sponsor_2_district,
            sponsor_3_name, sponsor_3_role, sponsor_3_party, sponsor_3_district,
            sponsor_4_name, sponsor_4_role, sponsor_4_party, sponsor_4_district,
            sponsor_5_name, sponsor_5_role, sponsor_5_party, sponsor_5_district,
            sponsor_6_name, sponsor_6_role, sponsor_6_party, sponsor_6_district,
            sponsor_7_name, sponsor_7_role, sponsor_7_party, sponsor_7_district,
            sponsor_8_name, sponsor_8_role, sponsor_8_party, sponsor_8_district,
            sponsor_9_name, sponsor_9_role, sponsor_9_party, sponsor_9_district,
            sponsor_10_name, sponsor_10_role, sponsor_10_party, sponsor_10_district,
            sponsor_11_name, sponsor_11_role, sponsor_11_party, sponsor_11_district,
            sponsor_12_name, sponsor_12_role, sponsor_12_party, sponsor_12_district,
            sponsor_13_name, sponsor_13_role, sponsor_13_party, sponsor_13_district,
            sponsor_14_name, sponsor_14_role, sponsor_14_party, sponsor_14_district,
            sponsor_15_name, sponsor_15_role, sponsor_15_party, sponsor_15_district,
            sponsor_16_name, sponsor_16_role, sponsor_16_party, sponsor_16_district,
            sponsor_17_name, sponsor_17_role, sponsor_17_party, sponsor_17_district,
            sponsor_18_name, sponsor_18_role, sponsor_18_party, sponsor_18_district,
            sponsor_19_name, sponsor_19_role, sponsor_19_party, sponsor_19_district,
            sponsor_20_name, sponsor_20_role, sponsor_20_party, sponsor_20_district
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        identifier, title, bill_text, chamber,
        first_action_date, latest_action_date, latest_action_description, total_sponsors,
        sponsor_data['sponsor_1_name'], sponsor_data['sponsor_1_role'], sponsor_data['sponsor_1_party'], sponsor_data['sponsor_1_district'],
        sponsor_data['sponsor_2_name'], sponsor_data['sponsor_2_role'], sponsor_data['sponsor_2_party'], sponsor_data['sponsor_2_district'],
        sponsor_data['sponsor_3_name'], sponsor_data['sponsor_3_role'], sponsor_data['sponsor_3_party'], sponsor_data['sponsor_3_district'],
        sponsor_data['sponsor_4_name'], sponsor_data['sponsor_4_role'], sponsor_data['sponsor_4_party'], sponsor_data['sponsor_4_district'],
        sponsor_data['sponsor_5_name'], sponsor_data['sponsor_5_role'], sponsor_data['sponsor_5_party'], sponsor_data['sponsor_5_district'],
        sponsor_data['sponsor_6_name'], sponsor_data['sponsor_6_role'], sponsor_data['sponsor_6_party'], sponsor_data['sponsor_6_district'],
        sponsor_data['sponsor_7_name'], sponsor_data['sponsor_7_role'], sponsor_data['sponsor_7_party'], sponsor_data['sponsor_7_district'],
        sponsor_data['sponsor_8_name'], sponsor_data['sponsor_8_role'], sponsor_data['sponsor_8_party'], sponsor_data['sponsor_8_district'],
        sponsor_data['sponsor_9_name'], sponsor_data['sponsor_9_role'], sponsor_data['sponsor_9_party'], sponsor_data['sponsor_9_district'],
        sponsor_data['sponsor_10_name'], sponsor_data['sponsor_10_role'], sponsor_data['sponsor_10_party'], sponsor_data['sponsor_10_district'],
        sponsor_data['sponsor_11_name'], sponsor_data['sponsor_11_role'], sponsor_data['sponsor_11_party'], sponsor_data['sponsor_11_district'],
        sponsor_data['sponsor_12_name'], sponsor_data['sponsor_12_role'], sponsor_data['sponsor_12_party'], sponsor_data['sponsor_12_district'],
        sponsor_data['sponsor_13_name'], sponsor_data['sponsor_13_role'], sponsor_data['sponsor_13_party'], sponsor_data['sponsor_13_district'],
        sponsor_data['sponsor_14_name'], sponsor_data['sponsor_14_role'], sponsor_data['sponsor_14_party'], sponsor_data['sponsor_14_district'],
        sponsor_data['sponsor_15_name'], sponsor_data['sponsor_15_role'], sponsor_data['sponsor_15_party'], sponsor_data['sponsor_15_district'],
        sponsor_data['sponsor_16_name'], sponsor_data['sponsor_16_role'], sponsor_data['sponsor_16_party'], sponsor_data['sponsor_16_district'],
        sponsor_data['sponsor_17_name'], sponsor_data['sponsor_17_role'], sponsor_data['sponsor_17_party'], sponsor_data['sponsor_17_district'],
        sponsor_data['sponsor_18_name'], sponsor_data['sponsor_18_role'], sponsor_data['sponsor_18_party'], sponsor_data['sponsor_18_district'],
        sponsor_data['sponsor_19_name'], sponsor_data['sponsor_19_role'], sponsor_data['sponsor_19_party'], sponsor_data['sponsor_19_district'],
        sponsor_data['sponsor_20_name'], sponsor_data['sponsor_20_role'], sponsor_data['sponsor_20_party'], sponsor_data['sponsor_20_district']
        ))
        print(f"  Added {identifier} to database")
    else:
        print(f"  {identifier} already exists in database, skipping")

conn.commit()
conn.close()

