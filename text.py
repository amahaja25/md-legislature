import sqlite3 

conn = sqlite3.connect('bills.db')
cursor = conn.cursor()

cursor.execute("SELECT text FROM bills")   
all_info = cursor.fetchall()  

def categorize(text):
    text = text.lower()
    if "immigration" in text or "immigrant" in text or "immigrate" in text or "visa" in text:
        return "Immigration"
    elif "health care" in text or "healthcare" in text or "medicare" in text or "medicaid" in text:
        return "Health Care"
    elif ("university of maryland" in text or "umd" in text or 
          "university system of maryland" in text or "usm" in text or 
          "university" in text or "higher education" in text):
        return "Higher Education"
    else:
        return "Other"

for (t,) in all_info:   
    print(t[:80], "...", "->", categorize(t))  
