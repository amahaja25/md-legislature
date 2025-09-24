import requests
import json

API_KEY = "6eb83043-1306-468e-b2ea-55ea1fd9810f"
headers = {"X-API-KEY": API_KEY}

params = {
    "jurisdiction": "Maryland",
    "session": "2025",
    "per_page": 5,
    "include": "sponsorships"
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
