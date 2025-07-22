import os
import logging
import re
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import Defaults
import gspread
from google.oauth2.service_account import Credentials

# Setup logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Load env
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set.")

# Google Sheets config
SHEET_NAME = "Telegram_Expense_Tracker"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("google_creds.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# Add header if missing
if not sheet.get_all_values() or sheet.row_values(1) != ["Date", "Time", "Amount", "Description"]:
    sheet.update("A1:D1", [["Date", "Time", "Amount", "Description"]])

# Message parser
def extract_details(text):
    try:
        text = text.replace("\n", " ").strip()
        date_match = re.search(r'on (\d{1,2}-[A-Za-z]{3}-\d{2})', text, re.IGNORECASE)
        amount_match = re.search(r'Rs\.?\s*(\d+[.]?\d*)', text, re.IGNORECASE)
        desc_match = re.search(r';\s*(.*?)\s*credited', text, re.IGNORECASE)

        if date_match and amount_match:
            dt = datetime.strptime(date_match.group(1), "%d-%b-%y")
            time_str = datetime.now().strftime("%H:%M")
            amount = float(amount_match.group(1))
            description = desc_match.group(1).strip() if desc_match else "Unknown"
            return dt.strftime("%d-%b-%y"), time_str, amount, description
    except Exception as e:
        logging.error("Parsing error: %s", e)
    return None

# Pull latest messages from Telegram
def process_updates():
    bot = Bot(token=BOT_TOKEN, defaults=Defaults(parse_mode=ParseMode.HTML))
    updates = bot.get_updates()
    for update in updates:
        msg = update.message.text
        chat_id = update.message.chat_id
        result = extract_details(msg)
        if result:
            sheet.append_row(list(result))
            bot.send_message(chat_id, "✅ Expense recorded in Google Sheet.")
        else:
            bot.send_message(chat_id, "❌ Couldn't extract expense details.")

if __name__ == "__main__":
    process_updates()
