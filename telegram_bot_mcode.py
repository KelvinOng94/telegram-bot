
# telegram_bot_mcode.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes, ConversationHandler
)
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

# Google Sheets setup from env var JSON
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
sheet_client = gspread.authorize(creds)
sheet = sheet_client.open("Video MCode Tracker").sheet1

# Frame.io API setup
FRAMEIO_TOKEN = os.getenv("FRAMEIO_TOKEN")
FRAMEIO_PROJECT_ID = os.getenv("FRAMEIO_PROJECT_ID")

# Staff database with company
staff_db = {
    'G003': ('ARIF', 'GGG'), 'G004': ('ALYZZA', 'GGG'), 'G009': ('AZIM', 'GGG'), 'G011': ('AINA', 'GGG'),
    'G012': ('SAFIRA', 'GGG'), 'G014': ('BATRISYA', 'GGG'), 'G017': ('KELVIN', 'GGG'), 'G018': ('HAIDA', 'GGG'),
    'TCO2008': ('HAIKAL', 'TCO'), 'TCO2013': ('MIZAN', 'TCO'), 'TCO2014': ('ARINA', 'TCO'), 'TCO2015': ('JOE', 'TCO'),
    'TCO2034': ('AISYAH', 'TCO'), 'GGD001': ('JAYDEN', 'GGD'), 'GGD002': ('ANGAH', 'GGD'), 'GGD003': ('ALVIN', 'GGD'),
    'GGD004': ('RAI', 'GGD'), 'GGD005': ('ATIKA (ADMIN)', 'GGD'), 'GGD006': ('SHUHADA', 'GGD'),
    'KS001': ('SHAZ', 'KSSB'), 'KS002': ('AFRIENA (ADMIN)', 'KSSB'), 'KS003': ('ANIS (ADMIN)', 'KSSB'),
    'KS004': ('FARHANA', 'KSSB'), 'KS005': ('SHAZWA - RESIGN', 'KSSB'), 'WJ001': ('SHAO EN', 'WJ')
}

# Session states
VIDEO, STAFF_ID, CONFIRM_NAME = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Please upload your first video.")
    return VIDEO

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['video'] = update.message.video
    context.user_data['timestamp'] = update.message.date
    await update.message.reply_text("Thank you. Please enter your Staff ID (e.g. G017).")
    return STAFF_ID

async def handle_staff_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    staff_id = update.message.text.strip().upper()
    context.user_data['staff_id'] = staff_id
    staff_info = staff_db.get(staff_id)
    if staff_info:
        name, company = staff_info
        context.user_data['staff_name'] = name
        context.user_data['company'] = company
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='yes')],
            [InlineKeyboardButton("No", callback_data='no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Is this correct?\n\nStaff ID: {staff_id}\nName: {name}",
            reply_markup=reply_markup
        )
        return CONFIRM_NAME
    else:
        await update.message.reply_text("Staff ID not found. Please enter a valid Staff ID.")
        return STAFF_ID

async def confirm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'yes':
        staff_id = context.user_data['staff_id']
        staff_name = context.user_data['staff_name']
        company = context.user_data['company']
        dt = context.user_data['timestamp']
        now = dt.astimezone()
        date_str = now.strftime('%Y-%m-%d')
        day_str = now.strftime('%A')
        time_str = now.strftime('%H:%M:%S')

        # Generate M code
        records = sheet.get_all_records()
        latest_mcode = {}
        for row in records:
            sid = row['STAFF ID']
            code = row.get('New M Code', '')
            if sid and code:
                num = int(code.split('_M')[-1])
                if sid not in latest_mcode or num > int(latest_mcode[sid].split('_M')[-1]):
                    latest_mcode[sid] = code
        last_code = latest_mcode.get(staff_id, f"{staff_id}_M0000")
        last_num = int(last_code.split('_M')[-1])
        new_num = last_num + 1
        new_mcode = f"{staff_id}_M{new_num:04d}"

        # Save to Google Sheet
        row_data = [date_str, day_str, time_str, company, f"{staff_id}_{staff_name}", '', new_mcode]
        sheet.append_row(row_data)

        await query.edit_message_text(
            f"✅ New M Code: {new_mcode}\nYour video has been received and recorded."
        )
        await query.message.reply_text("Do you want to upload another video?\n✅ Yes\n❌ No")
        return VIDEO
    else:
        await query.edit_message_text("Please re-enter your correct Staff ID.")
        return STAFF_ID

if __name__ == '__main__':
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            VIDEO: [MessageHandler(filters.VIDEO, handle_video), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video)],
            STAFF_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_staff_id)],
            CONFIRM_NAME: [CallbackQueryHandler(confirm_name)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()
