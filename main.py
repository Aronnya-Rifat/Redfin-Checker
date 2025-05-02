import os
import time
import logging
import requests
import pandas as pd
from lxml import html
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIGURATION ===
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
WORKSHEET_NAME = os.getenv('WORKSHEET_NAME', 'listings to submit')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')
URL_COLUMN = 'URL'
STATUS_COLUMN = 'Live Status'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

logging.basicConfig(level=logging.INFO)

def get_redfin_status(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        tree = html.fromstring(res.content)
        status = tree.xpath('//*[@id="content"]/div[8]/div[2]/div[1]/div[1]/section/div/div/div/div[1]/div[1]/span/text()')
        return status[0].strip() if status else 'Unknown'
    except Exception as e:
        logging.error(f"Failed to get status for {url}: {e}")
        return 'Error'

def main():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)

        worksheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_values()
        headers = data[0]
        df = pd.DataFrame(data[1:], columns=headers)

        if URL_COLUMN not in df.columns:
            logging.error(f"Missing column: {URL_COLUMN}")
            return

        if STATUS_COLUMN not in df.columns:
            logging.info(f"Adding missing column: {STATUS_COLUMN}")
            worksheet.update_cell(1, len(headers) + 1, STATUS_COLUMN)
            df[STATUS_COLUMN] = ''
            status_col_index = len(headers)
        else:
            status_col_index = df.columns.get_loc(STATUS_COLUMN)

        statuses = []
        for url in df[URL_COLUMN]:
            status = get_redfin_status(url)
            logging.info(f"{url} -> {status}")
            statuses.append(status)
            time.sleep(1)

        cell_range = f"{chr(65 + status_col_index)}2:{chr(65 + status_col_index)}{len(statuses) + 1}"
        cell_list = worksheet.range(cell_range)
        for i, cell in enumerate(cell_list):
            cell.value = statuses[i]
        worksheet.update_cells(cell_list)

        logging.info("✅ Batch update complete.")
    except Exception as e:
        logging.critical(f"Unexpected error in main(): {e}", exc_info=True)

if __name__ == "__main__":
    main()
