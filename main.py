import pandas as pd
import requests
import time
from lxml import html
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIGURATION ===
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
WORKSHEET_NAME = os.environ.get('WORKSHEET_NAME', 'listings to submit')
URL_COLUMN = 'URL'
STATUS_COLUMN = 'Live Status'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# === Get Listing Status from Redfin Page ===
def get_redfin_status(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        tree = html.fromstring(res.content)
        status = tree.xpath('//*[@id="content"]/div[8]/div[2]/div[1]/div[1]/section/div/div/div/div[1]/div[1]/span/text()')
        if status:
            return status[0].strip()
        else:
            return 'Unknown'
    except Exception as e:
        return 'Error'

# === Main Script ===
def main():
    # Auth using credentials from environment variable
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not credentials_json:
        print("❌ GOOGLE_CREDENTIALS_JSON environment variable not found.")
        return

    creds_dict = json.loads(credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Open Sheet and Tab
    worksheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(WORKSHEET_NAME)
    data = worksheet.get_all_values()
    headers = data[0]
    df = pd.DataFrame(data[1:], columns=headers)

    # Ensure required columns exist
    if URL_COLUMN not in df.columns:
        print(f"❌ Missing column: {URL_COLUMN}")
        return

    if STATUS_COLUMN not in df.columns:
        print(f"➕ Adding missing column: {STATUS_COLUMN}")
        worksheet.update_cell(1, len(headers) + 1, STATUS_COLUMN)
        df[STATUS_COLUMN] = ''
        status_col_index = len(headers)  # zero-based
    else:
        status_col_index = df.columns.get_loc(STATUS_COLUMN)

    # Process Redfin URLs
    statuses = []
    for url in df[URL_COLUMN]:
        status = get_redfin_status(url)
        print(f"{url} -> {status}")
        statuses.append(status)
        time.sleep(1)  # polite delay

    # === Batch Update ===
    cell_range = f"{chr(65 + status_col_index)}2:{chr(65 + status_col_index)}{len(statuses) + 1}"
    cell_list = worksheet.range(cell_range)
    for i, cell in enumerate(cell_list):
        cell.value = statuses[i]
    worksheet.update_cells(cell_list)

    print("✅ Batch update complete.")

if __name__ == "__main__":
    script = "https://script.google.com/macros/s/AKfycbzpMZGPduBMNJsX_8pafv7RUVosMNqj23gp4o2A1m_354o1vjIC2iQ-eTDM1Ch38LhM/exec"
    main()
    response = requests.post(script_url, json={"action": "manualSync"})
    print(response.text)
    
