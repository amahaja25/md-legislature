import requests
import json

API_KEY = "6eb83043-1306-468e-b2ea-55ea1fd9810f"
headers = {"X-API-KEY": API_KEY}

params = {
    "jurisdiction": "Maryland",
    "session": "2025",
    "per_page": 5
}

response = requests.get("https://v3.openstates.org/bills", headers=headers, params=params)
data = response.json()

print(json.dumps(data, indent=4))
# bills endpoint has ID, house/senate, classification, date effective, created date, updated date, first action date, latest action date, openstates url, latest action description, latest passage date.

sponsors_response = requests.get("https://v3.openstates.org/people", headers=headers, params=params)
sponsors_data = sponsors_response.json()
print(json.dumps(sponsors_data, indent=4))
# sponsors endpoint has ID, name, party, role, upper/lower, district,contact info, image, gender, birthdate, openstates url

# there doesn't seem to be a way to connect the bills to an individual sponsor. even at the individual bill level, there is no information about the sponsor of said bill.

for bill in data.get("results", []):
    identifier = bill.get("identifier")
    title = bill.get("title")
    print(f"Bill: {identifier} - {title}") 
       
    sponsorships = bill.get("sponsorships", [])
    if sponsorships:
        print("  Sponsors:")
        for s in sponsorships:
            name = s.get("name", "Unknown")
            role = s.get("classification", "sponsor")
            primary = " (primary)" if s.get("primary") else ""
            print(f"    - {name} [{role}]{primary}")
    
    else:
        print("  No sponsors found")
        # getting no sponsors found for each bill 
