
import os
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_NAME = "Telegram_Expense_Tracker"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("google_creds.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# Set header if empty
if sheet.row_count == 0 or sheet.row_values(1) != ["Date", "Time", "Amount", "Description"]:
    sheet.update("A1:D1", [["Date", "Time", "Amount", "Description"]])

def extract_details(text):
    try:
        date_match = re.search(r'on (\d{1,2}-[A-Za-z]{3}-\d{2})', text)
        amount_match = re.search(r'for Rs (\d+[.]?\d*)', text)
        desc_match = re.search(r'credited\.?(.*?)UPI', text)

        if date_match and amount_match:
            dt = datetime.strptime(date_match.group(1), "%d-%b-%y")
            time_str = datetime.now().strftime("%H:%M")
            amount = float(amount_match.group(1))
            description = desc_match.group(1).strip() if desc_match else "Unknown"
            return dt.strftime("%d-%b-%y"), time_str, amount, description
    except Exception as e:
        print("Parsing error:", e)
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = extract_details(text)
    if result:
        sheet.append_row(list(result))
        await update.message.reply_text("✅ Expense recorded to Google Sheet.")
    else:
        await update.message.reply_text("❌ Couldn't extract details.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is running...")
    app.run_polling()
