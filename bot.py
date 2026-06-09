import os
import re
import csv
import requests
from io import StringIO
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters


BOT_TOKEN = os.getenv("BOT_TOKEN")
ZEROBOUNCE_API_KEY = os.getenv("ZEROBOUNCE_API_KEY")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def map_status(zb_status, zb_sub_status):
    status = (zb_status or "").lower()
    sub = (zb_sub_status or "").lower()

    if status == "valid":
        return "Live", "Active & deliverable", "green"

    if status == "invalid":
        return "Not Exist", f"Invalid email / {sub}", "gray"

    if status == "catch-all":
        return "Verify", "Catch-all domain, cannot confirm mailbox without bounce", "orange"

    if status == "do_not_mail":
        return "Disable", f"Do not mail / {sub}", "red"

    if status == "spamtrap":
        return "Disable", "Spamtrap email", "red"

    if status == "abuse":
        return "Disable", "Abuse email", "red"

    if status == "unknown":
        return "Verify", f"Unknown / {sub}", "orange"

    return "Verify", f"Unclear result: {zb_status} / {zb_sub_status}", "orange"


def check_email(email):
    email = email.strip().lower()

    result = {
        "Email": email,
        "Trạng thái": "Verify",
        "Lý do": "",
        "Màu sắc": "orange",
        "ZeroBounce Status": "",
        "ZeroBounce Sub Status": "",
        "Thời gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if not EMAIL_RE.match(email):
        result["Trạng thái"] = "Invalid format"
        result["Lý do"] = "Invalid email syntax"
        result["Màu sắc"] = "red"
        return result

    try:
        url = "https://api.zerobounce.net/v2/validate"
        params = {
            "api_key": ZEROBOUNCE_API_KEY,
            "email": email,
            "ip_address": "",
        }

        r = requests.get(url, params=params, timeout=40)
        data = r.json()

        zb_status = data.get("status", "")
        zb_sub_status = data.get("sub_status", "")

        status, reason, color = map_status(zb_status, zb_sub_status)

        result["Trạng thái"] = status
        result["Lý do"] = reason
        result["Màu sắc"] = color
        result["ZeroBounce Status"] = zb_status
        result["ZeroBounce Sub Status"] = zb_sub_status

        return result

    except Exception as e:
        result["Trạng thái"] = "Verify"
        result["Lý do"] = f"API error: {str(e)}"
        result["Màu sắc"] = "orange"
        return result


def make_csv(rows):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xin chào!\n\n"
        "Dùng lệnh:\n"
        "/check a@gmail.com b@example.com\n\n"
        "Hoặc upload file .txt/.csv chứa danh sách email."
    )


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emails = context.args

    if not emails:
        await update.message.reply_text("Ví dụ: /check a@gmail.com b@example.com")
        return

    await update.message.reply_text(f"Đang kiểm tra {len(emails)} email...")

    rows = [check_email(email) for email in emails]
    csv_data = make_csv(rows)

    await update.message.reply_document(
        document=csv_data,
        filename="email_check_result.csv",
        caption=f"Đã kiểm tra {len(rows)} email."
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.endswith((".txt", ".csv")):
        await update.message.reply_text("Chỉ hỗ trợ file .txt hoặc .csv.")
        return

    file = await doc.get_file()
    content = await file.download_as_bytearray()
    text = content.decode("utf-8", errors="ignore")

    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)

    if not emails:
        await update.message.reply_text("Không tìm thấy email trong file.")
        return

    emails = list(dict.fromkeys([e.lower() for e in emails]))

    await update.message.reply_text(f"Đang kiểm tra {len(emails)} email...")

    rows = [check_email(email) for email in emails]
    csv_data = make_csv(rows)

    await update.message.reply_document(
        document=csv_data,
        filename="email_check_result.csv",
        caption=f"Đã kiểm tra {len(rows)} email."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Missing BOT_TOKEN")

    if not ZEROBOUNCE_API_KEY:
        raise RuntimeError("Missing ZEROBOUNCE_API_KEY")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("BOT STARTED SUCCESSFULLY")
    app.run_polling()


if __name__ == "__main__":
    main()
