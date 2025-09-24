import requests
import json
import sqlite3

# set API key and headers
API_KEY = "4dca6d1d-5c67-4cc3-8c68-8ca754b4f158"
headers = {"X-API-KEY": API_KEY}

params = {
    "jurisdiction": "Maryland",
    "session": "2025",
    "per_page": 5, # for testing, just keep 5 bills
    "include": "sponsorships" # important! won't get sponsors without this line.
}

response = requests.get("https://v3.openstates.org/bills", headers=headers, params=params)
data = response.json()

print(json.dumps(data, indent=4))



for bill in data.get("results", []):
    identifier = bill.get("identifier")
    title = bill.get("title")
    print(f"Bill: {identifier} - {title}") 
       
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
        full_name TEXT
    )
''')

# Insert the bill info into sqlite3 db 
for bill in data.get("results", []):
    identifier = bill.get("identifier")
    title = bill.get("title")
    
    sponsorships = bill.get("sponsorships", [])
    if sponsorships:
        for s in sponsorships:
            person = s.get("person", {})
            full_name = person.get("name", s.get("name", "Unknown"))
            role = s.get("classification", "sponsor")
            
            cursor.execute('''
                INSERT INTO bills (identifier, title, sponsor, role, classification, full_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (identifier, title, s.get("name", "Unknown"), role, s.get("classification", ""), full_name))
    else:
        # Insert bill with no sponsor
        cursor.execute('''
            INSERT INTO bills (identifier, title, sponsor, role, classification, full_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (identifier, title, None, None, None, None))

conn.commit()
conn.close()

