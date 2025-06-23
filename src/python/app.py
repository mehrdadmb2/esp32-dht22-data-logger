#!/usr/bin/env python3
import os
import sys
import subprocess
import importlib
import platform
import time
import datetime
import logging
import threading
import asyncio

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTextEdit, QSplitter
)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QTimer

# ==================== Logging Configuration ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("esp32_data_logger.log", encoding='utf-8')
    ]
)

# ==================== Auto Lib Downloader ====================
def auto_lib_downloader(libs):
    python_executable = sys.executable
    for lib in libs:
        try:
            importlib.import_module(lib)
            logging.info(f"[✅] Library '{lib}' imported successfully.")
        except ImportError:
            logging.warning(f"[⚠️] Library '{lib}' is not installed. Installing...")
            result = subprocess.run(
                [python_executable, "-m", "pip", "install", lib],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                logging.info(f"[✅] Library '{lib}' installed successfully.")
            else:
                logging.error(f"[❌] Failed to install '{lib}'. Error:\n{result.stderr}")

required_libs = [
    'pandas',
    'openpyxl',
    'requests',
    'colorama',
    'matplotlib',
    'python-telegram-bot',
    'PyQt5'
]
auto_lib_downloader(required_libs)

# ==================== Imports After Installation ====================
from colorama import init, Fore
init(autoreset=True)
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# telegram bot imports
try:
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError:
    logging.error("Could not import python-telegram-bot library. Make sure it is installed.")

# ==================== Configuration ====================
BOT_TOKEN = "yor token"  # توکن ربات
ADMIN_IDS = [381200758]  # آیدی ادمین‌ها
ESP32_DATA_URL = "http://192.168.1.115/data"
OUTPUT_DIRECTORY = "Z:\\ESP32"  # مسیر ذخیره فایل‌ها
EXCEL_FILE_PREFIX = "data_log_"

# ==================== Helper: Clear Screen ====================
def clear():
    os.system('cls' if platform.system() == "Windows" else 'clear')
clear()

# ==================== Fetch Public IP ====================
def fetch_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=30)
        response.raise_for_status()
        return response.json().get("ip", "N/A")
    except requests.RequestException as e:
        logging.error(f"[❌] Error fetching public IP: {e}")
        return "N/A"

# ==================== Fetch Data From ESP32 ====================
def fetch_data():
    try:
        response = requests.get(ESP32_DATA_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        required_keys = [
            "time", "date", "localTemperature", "localHumidity",
            "internetTemperature", "internetHumidity", "buy_price",
            "sell_price", "gold_price", "ping", "devices"
        ]
        if all(key in data for key in required_keys):
            logging.info(Fore.GREEN + "[✅] Data received successfully.")
            return data
        else:
            logging.error(Fore.RED + "[❌] The received data structure from ESP32 is incorrect.")
            return None
    except requests.RequestException as e:
        logging.error(Fore.RED + f"[❌] Error fetching data: {e}")
        return None

# ==================== Save Data To Excel ====================
def save_to_excel(data):
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"{EXCEL_FILE_PREFIX}{today}.xlsx"
        full_path = os.path.join(OUTPUT_DIRECTORY, filename)
        df_new = pd.DataFrame([{
            "Time": data["time"],
            "Date": data["date"],
            "Local Temperature": data["localTemperature"],
            "Local Humidity": data["localHumidity"],
            "Internet Temperature": data["internetTemperature"],
            "Internet Humidity": data["internetHumidity"],
            "Buy Price": data["buy_price"],
            "Sell Price": data["sell_price"],
            "Gold Price": data["gold_price"],
            "Ping Status": "Success" if data["ping"] != "Fail" else "Failed",
            "Ping Number": data["ping"] if data["ping"] != "Fail" else None,
            "Devices": str(data["devices"])
        }])
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        if os.path.exists(full_path):
            try:
                df_existing = pd.read_excel(full_path, engine="openpyxl")
            except Exception as e:
                logging.error(f"[❌] Error reading existing Excel file: {e}. Recreating file.")
                os.remove(full_path)
                df_existing = pd.DataFrame()
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_excel(full_path, index=False, engine="openpyxl")
        logging.info(Fore.GREEN + f"[✅] Data saved to {full_path}.")
    except Exception as e:
        logging.error(Fore.RED + f"[❌] Error saving data to Excel: {e}")

# ==================== Get DataFrame for Timeframe ====================
def get_dataframe_for_timeframe(timeframe):
    try:
        if timeframe in ["1h", "1d"]:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            file = os.path.join(OUTPUT_DIRECTORY, f"{EXCEL_FILE_PREFIX}{today}.xlsx")
            if not os.path.exists(file):
                return None, "📂 Today's file is missing."
            df = pd.read_excel(file, engine="openpyxl")
        elif timeframe == "1w":
            days_required = 7
            dfs = []
            for i in range(days_required):
                date_str = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                file = os.path.join(OUTPUT_DIRECTORY, f"{EXCEL_FILE_PREFIX}{date_str}.xlsx")
                if os.path.exists(file):
                    dfs.append(pd.read_excel(file, engine="openpyxl"))
                else:
                    logging.warning(f"[⚠️] File for {date_str} is missing; skipping.")
            if not dfs or len(dfs) < days_required:
                return None, f"📂 Insufficient files for weekly chart. Found {len(dfs)}/{days_required}"
            df = pd.concat(dfs, ignore_index=True)
        elif timeframe == "1m":
            days_required = 30
            dfs = []
            for i in range(days_required):
                date_str = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                file = os.path.join(OUTPUT_DIRECTORY, f"{EXCEL_FILE_PREFIX}{date_str}.xlsx")
                if os.path.exists(file):
                    dfs.append(pd.read_excel(file, engine="openpyxl"))
                else:
                    logging.warning(f"[⚠️] File for {date_str} is missing; skipping.")
            if not dfs or len(dfs) < int(days_required * 0.7):
                return None, f"📂 Insufficient files for monthly chart. Found {len(dfs)}/{days_required}"
            df = pd.concat(dfs, ignore_index=True)
        else:
            return None, "❌ Invalid timeframe."
        try:
            df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logging.warning(f"[⚠️] Failed to combine date/time: {e}")
            df["DateTime"] = pd.to_datetime(df["Time"], format="%H:%M:%S", errors="coerce")
        df = df.dropna(subset=["DateTime"])
        df.sort_values(by="DateTime", inplace=True)
        if timeframe == "1h" and not df.empty:
            max_time = df["DateTime"].max()
            df = df[df["DateTime"] >= max_time - datetime.timedelta(hours=1)]
        return df, None
    except Exception as e:
        logging.error(f"[❌] Error in get_dataframe_for_timeframe: {e}")
        return None, str(e)

# ==================== Generate Chart ====================
def generate_chart(chart_type="weather", timeframe="1d"):
    try:
        df, error = get_dataframe_for_timeframe(timeframe)
        if error:
            logging.error(error)
            return None
        if df.empty:
            logging.error("📂 No data available after filtering for the selected timeframe.")
            return None

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))

        if chart_type == "weather":
            ax2 = ax.twinx()
            ax.plot(df["DateTime"], df["Local Temperature"], color='red', label='Temp (°C)', linewidth=1.5, marker='')
            ax2.plot(df["DateTime"], df["Local Humidity"], color='cyan', label='Humidity (%)', linewidth=1.5, marker='')
            ax.set_ylabel("Temp (°C)", color='red', fontsize=12)
            ax2.set_ylabel("Humidity (%)", color='cyan', fontsize=12)
            temp_max = df["Local Temperature"].max()
            temp_min = df["Local Temperature"].min()
            row_max_temp = df.loc[df["Local Temperature"].idxmax()]
            row_min_temp = df.loc[df["Local Temperature"].idxmin()]
            ax.annotate(f"Max: {temp_max:.1f}°C", xy=(row_max_temp["DateTime"], temp_max),
                        xytext=(0, 15), textcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax.annotate(f"Min: {temp_min:.1f}°C", xy=(row_min_temp["DateTime"], temp_min),
                        xytext=(0, -20), textcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='white'), color='white')
            hum_max = df["Local Humidity"].max()
            hum_min = df["Local Humidity"].min()
            row_max_hum = df.loc[df["Local Humidity"].idxmax()]
            row_min_hum = df.loc[df["Local Humidity"].idxmin()]
            ax2.annotate(f"Max: {hum_max:.1f}%", xy=(row_max_hum["DateTime"], hum_max),
                         xytext=(0, 15), textcoords="offset points",
                         arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax2.annotate(f"Min: {hum_min:.1f}%", xy=(row_min_hum["DateTime"], hum_min),
                         xytext=(0, -20), textcoords="offset points",
                         arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax.set_title(f"Weather Chart ({timeframe})", color='white', fontsize=14)
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines + lines2, labels + labels2, loc='best', fontsize=11)
        elif chart_type == "gold":
            ax.plot(df["DateTime"], df["Gold Price"], color='gold', label='Gold Price', linewidth=1.5, marker='')
            gold_max = df["Gold Price"].max()
            gold_min = df["Gold Price"].min()
            row_max_gold = df.loc[df["Gold Price"].idxmax()]
            row_min_gold = df.loc[df["Gold Price"].idxmin()]
            ax.annotate(f"Max: {gold_max:.1f}", xy=(row_max_gold["DateTime"], gold_max),
                        xytext=(0, 15), textcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax.annotate(f"Min: {gold_min:.1f}", xy=(row_min_gold["DateTime"], gold_min),
                        xytext=(0, -20), textcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax.set_ylabel("Gold Price", color='gold', fontsize=12)
            ax.set_title(f"Gold Chart ({timeframe})", color='white', fontsize=14)
            ax.legend(loc='best', fontsize=11)
        elif chart_type == "dollar":
            ax.plot(df["DateTime"], df["Sell Price"], color='lime', label='Dollar Price', linewidth=1.5, marker='')
            dollar_max = df["Sell Price"].max()
            dollar_min = df["Sell Price"].min()
            row_max_dollar = df.loc[df["Sell Price"].idxmax()]
            row_min_dollar = df.loc[df["Sell Price"].idxmin()]
            ax.annotate(f"Max: {dollar_max:.1f}", xy=(row_max_dollar["DateTime"], dollar_max),
                        xytext=(0, 15), textcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax.annotate(f"Min: {dollar_min:.1f}", xy=(row_min_dollar["DateTime"], dollar_min),
                        xytext=(0, -20), textcoords="offset points",
                        arrowprops=dict(arrowstyle="->", color='white'), color='white')
            ax.set_ylabel("Dollar Price", color='lime', fontsize=12)
            ax.set_title(f"Dollar Chart ({timeframe})", color='white', fontsize=14)
            ax.legend(loc='best', fontsize=11)
        else:
            logging.error("❌ Invalid chart type.")
            return None

        ax.set_xlabel("Time", color='white', fontsize=12)
        ax.tick_params(axis='x', labelcolor='white')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        fig.autofmt_xdate()
        ax.grid(True, which='major', linestyle='--', alpha=0.5)

        chart_path = os.path.join(OUTPUT_DIRECTORY, "chart.png")
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        logging.info(Fore.GREEN + f"[✅] Chart saved to {chart_path}.")
        return chart_path

    except Exception as e:
        logging.error(Fore.RED + f"[❌] Error generating chart: {e}")
        return None

# ==================== Get Latest Data from Excel ====================
def get_latest_data():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"{EXCEL_FILE_PREFIX}{today}.xlsx"
        full_path = os.path.join(OUTPUT_DIRECTORY, filename)
        if os.path.exists(full_path):
            df = pd.read_excel(full_path, engine="openpyxl")
            if not df.empty:
                return df.iloc[-1].to_dict()
        return None
    except Exception as e:
        logging.error(f"[❌] Error reading latest data: {e}")
        return None

# ==================== Log User Request ====================
def log_user_request(user_id, username, first_name, last_name, request_type, request_data):
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"user_requests_{today}.xlsx"
        full_path = os.path.join(OUTPUT_DIRECTORY, filename)
        df_new = pd.DataFrame([{
            "User ID": user_id,
            "Username": username,
            "Full Name": f"{first_name} {last_name}",
            "Request Type": request_type,
            "Request Data": request_data,
            "Date": today,
            "Time": datetime.datetime.now().strftime("%H:%M:%S")
        }])
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
        if os.path.exists(full_path):
            df_existing = pd.read_excel(full_path, engine="openpyxl")
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_excel(full_path, index=False, engine="openpyxl")
        logging.info(Fore.GREEN + f"[✅] User request logged in {full_path}.")
    except Exception as e:
        logging.error(Fore.RED + f"[❌] Error logging user request: {e}")

# -------------------------------------------------------------
#               Telegram Handlers & Bot Logic
# -------------------------------------------------------------
async def start_command(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_request(user.id, user.username, user.first_name, user.last_name or "", "/start", "🤖 Start Bot")
    text = (
        "🌟 سلام! به ربات ESP32 خوش آمدید.\n"
        "📡 دستورات موجود:\n"
        "• /esp32 → دریافت آخرین داده‌های دستگاه\n"
        "• /esp32_all → دریافت فایل اکسل امروز\n"
        "• /chart → مشاهده منوی چارت‌ها\n"
        "• /admin → پنل ادمین (فقط برای مدیران)\n"
    )
    await update.message.reply_text(text)

async def esp32_command(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_request(user.id, user.username, user.first_name, user.last_name or "", "/esp32", "📡 Fetch Data")
    data = fetch_data()
    public_ip = fetch_public_ip()
    if not data:
        data = get_latest_data()
    if data:
        msg = (
            f"🕒 Time: {data.get('time', '')}\n"
            f"📅 Date: {data.get('date', '')}\n"
            f"🌡️ Local Temp: {data.get('localTemperature', '')}°C\n"
            f"💧 Local Humidity: {data.get('localHumidity', '')}%\n"
            f"🌡️ Internet Temp: {data.get('internetTemperature', '')}°C\n"
            f"💧 Internet Humidity: {data.get('internetHumidity', '')}%\n"
            f"💲 Buy Price: {data.get('buy_price', '')}\n"
            f"💵 Sell Price: {data.get('sell_price', '')}\n"
            f"🥇 Gold Price: {data.get('gold_price', '')}\n"
            f"📶 Ping: {data.get('ping', 'Fail')}\n"
            f"📡 Devices: {data.get('devices', '')}\n"
            f"🌐 Public IP: {public_ip}"
        )
        try:
            save_to_excel(data)
        except Exception as ex:
            logging.error(f"[❌] Error in saving data: {ex}")
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ هیچ داده‌ای موجود نیست.")

async def esp32_all_command(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_request(user.id, user.username, user.first_name, user.last_name or "", "/esp32_all", "📂 Retrieve Excel File")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{EXCEL_FILE_PREFIX}{today}.xlsx"
    full_path = os.path.join(OUTPUT_DIRECTORY, filename)
    if os.path.exists(full_path):
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(full_path, 'rb'), caption="📂 فایل اکسل امروز")
    else:
        await update.message.reply_text("❌ فایل اکسل امروز موجود نیست.")

# --------------------------
#  Chart Menu Implementation
# --------------------------
async def chart_command(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_request(user.id, user.username, user.first_name, user.last_name or "", "/chart", "📊 Show Chart Menu")
    keyboard = [
        [KeyboardButton("🌤️ چارت آب و هوا"), KeyboardButton("🥇 چارت طلا"), KeyboardButton("💵 چارت دلار")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("💡 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

async def handle_chart_text(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text in ["🌤️ چارت آب و هوا", "🥇 چارت طلا", "💵 چارت دلار"]:
        context.user_data["chart_type"] = text
        log_user_request(user.id, user.username, user.first_name, user.last_name or "", "chart_menu", f"Selected: {text}")
        keyboard = [
            [KeyboardButton("⏱️ نمودار 1 ساعته"), KeyboardButton("📅 نمودار 1 روزه")],
            [KeyboardButton("📊 نمودار هفتگی"), KeyboardButton("📈 نمودار ماهانه")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("⌚ لطفاً بازه‌ی زمانی را انتخاب کنید:", reply_markup=reply_markup)
        return

    if text in ["⏱️ نمودار 1 ساعته", "📅 نمودار 1 روزه", "📊 نمودار هفتگی", "📈 نمودار ماهانه"]:
        chart_type = context.user_data.get("chart_type", "🌤️ چارت آب و هوا")
        timeframe = text
        log_user_request(user.id, user.username, user.first_name, user.last_name or "", "chart_timeframe", f"{chart_type} - {timeframe}")

        internal_chart_type = "weather"
        if chart_type == "🥇 چارت طلا":
            internal_chart_type = "gold"
        elif chart_type == "💵 چارت دلار":
            internal_chart_type = "dollar"

        internal_timeframe = "1h"
        if timeframe == "📅 نمودار 1 روزه":
            internal_timeframe = "1d"
        elif timeframe == "📊 نمودار هفتگی":
            internal_timeframe = "1w"
        elif timeframe == "📈 نمودار ماهانه":
            internal_timeframe = "1m"

        chart_path = generate_chart(chart_type=internal_chart_type, timeframe=internal_timeframe)
        if chart_path and os.path.exists(chart_path):
            await update.message.reply_photo(photo=open(chart_path, 'rb'), caption=f"{chart_type} - {timeframe}")
        else:
            await update.message.reply_text("❌ نموداری برای این بازه در دسترس نیست.")
        return

# --------------------------
#       Admin Commands
# --------------------------
async def admin_command(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی ادمین ندارید!")
        log_user_request(user.id, user.username, user.first_name, user.last_name or "", "/admin", "Access Denied")
        return
    log_user_request(user.id, user.username, user.first_name, user.last_name or "", "/admin", "Access Granted")
    keyboard = [
        [KeyboardButton("📂 ارسال کل فایل‌های اکسل"), KeyboardButton("📂 ارسال کل فایل‌های لاگ")],
        [KeyboardButton("📜 نمایش لاگ‌ها به صورت متن")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("🔐 پنل ادمین:", reply_markup=reply_markup)

async def handle_admin_text(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if user.id not in ADMIN_IDS:
        return
    if text == "📂 ارسال کل فایل‌های اکسل":
        log_user_request(user.id, user.username, user.first_name, user.last_name or "", "admin", "Send all excel files")
        await send_all_excel_files(update, context)
    elif text == "📂 ارسال کل فایل‌های لاگ":
        log_user_request(user.id, user.username, user.first_name, user.last_name or "", "admin", "Send all log files")
        await send_all_log_files(update, context)
    elif text == "📜 نمایش لاگ‌ها به صورت متن":
        log_user_request(user.id, user.username, user.first_name, user.last_name or "", "admin", "View logs as text")
        await view_log_as_text(update, context)

async def send_all_excel_files(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        excel_files = [f for f in os.listdir(OUTPUT_DIRECTORY) if f.endswith(".xlsx") and f.startswith("data_log_")]
        if not excel_files:
            await update.message.reply_text("🚫 هیچ فایل اکسل موجود نیست!")
            return
        for file in excel_files:
            file_path = os.path.join(OUTPUT_DIRECTORY, file)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))
        await update.message.reply_text("✅ تمام فایل‌های اکسل ارسال شدند.")
    except Exception as e:
        logging.error(f"[❌] Error sending Excel files: {e}")
        await update.message.reply_text("❌ خطا در ارسال فایل‌های اکسل!")

async def send_all_log_files(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        log_files = [f for f in os.listdir(OUTPUT_DIRECTORY) if f.startswith("user_requests_") and f.endswith(".xlsx")]
        if not log_files:
            await update.message.reply_text("🚫 هیچ فایل لاگ موجود نیست!")
            return
        for file in log_files:
            file_path = os.path.join(OUTPUT_DIRECTORY, file)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))
        await update.message.reply_text("✅ تمام فایل‌های لاگ ارسال شدند.")
    except Exception as e:
        logging.error(f"[❌] Error sending log files: {e}")
        await update.message.reply_text("❌ خطا در ارسال فایل‌های لاگ!")

async def view_log_as_text(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file_path = os.path.join(OUTPUT_DIRECTORY, f"user_requests_{today}.xlsx")
        if not os.path.exists(log_file_path):
            await update.message.reply_text("🚫 فایل لاگ برای امروز موجود نیست!")
            return
        df = pd.read_excel(log_file_path, engine="openpyxl")
        text_logs = ""
        for idx, row in df.iterrows():
            text_logs += (
                f"Log Entry #{idx+1}\n"
                f"User ID: {row.get('User ID', '')}\n"
                f"Username: @{row.get('Username', '')}\n"
                f"Full Name: {row.get('Full Name', '')}\n"
                f"Request Type: {row.get('Request Type', '')}\n"
                f"Request Data: {row.get('Request Data', '')}\n"
                f"Date: {row.get('Date', '')}\n"
                f"Time: {row.get('Time', '')}\n"
                "----------------------------\n"
            )
        await update.message.reply_text(text_logs)
    except Exception as e:
        logging.error(f"[❌] Error reading log file: {e}")
        await update.message.reply_text("❌ خطا در خواندن فایل لاگ!")

# ==================== Telegram Bot Runner ====================
def run_telegram_bot():
    while True:
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            application = ApplicationBuilder().token(BOT_TOKEN).build()
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("esp32", esp32_command))
            application.add_handler(CommandHandler("esp32_all", esp32_all_command))
            application.add_handler(CommandHandler("chart", chart_command))
            application.add_handler(CommandHandler("admin", admin_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_text))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))
            logging.info("🤖 Telegram bot started successfully. Waiting for commands...")
            application.run_polling()
        except Exception as e:
            logging.error(f"[❌] Telegram bot error: {e}")
            logging.info("⏳ Retrying to connect Telegram Bot in 60 seconds...")
            time.sleep(60)

# ==================== Main Data Logging Loop ====================
def main_data_loop():
    logging.info(Fore.GREEN + "📡 Starting data logging from ESP32...")
    while True:
        try:
            data = fetch_data()
            if data:
                save_to_excel(data)
            else:
                logging.warning(Fore.YELLOW + "[⚠️] No data received in this cycle.")
        except Exception as e:
            logging.error(Fore.RED + f"[❌] Exception in data logging loop: {e}")
        time.sleep(60)

# ==================== Custom Logging Handler for GUI ====================
class GuiLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        # اضافه کردن متن به QTextEdit در GUI (در نخ اصلی)
        self.widget.append(msg)

# ==================== GUI: PyQt5 Chart Viewer with Log Display ====================
class ChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("رابط گرافیکی ESP32 - نمایش نمودار")
        self.setGeometry(100, 100, 1000, 700)
        self.current_chart_type = None
        self.current_timeframe = None
        self.refresh_interval = 5000  # 5000 میلی‌ثانیه = 5 ثانیه
        self.setup_ui()
        self.apply_dark_mode()
        self.start_auto_refresh()

    def setup_ui(self):
        # استفاده از QSplitter برای تقسیم صفحه بین نمودار و لاگ‌ها
        splitter = QSplitter(Qt.Vertical)
        self.setCentralWidget(splitter)

        # بخش بالایی: کنترل‌ها و نمایش نمودار
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        control_layout = QHBoxLayout()
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["چارت آب و هوا", "چارت طلا", "چارت دلار"])
        control_layout.addWidget(QLabel("نوع نمودار:"))
        control_layout.addWidget(self.chart_type_combo)

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["نمودار 1 ساعته", "نمودار 1 روزه", "نمودار هفتگی", "نمودار ماهانه"])
        control_layout.addWidget(QLabel("بازه زمانی:"))
        control_layout.addWidget(self.timeframe_combo)

        self.generate_button = QPushButton("تایید انتخاب و شروع بروزرسانی")
        self.generate_button.clicked.connect(self.on_start_chart)
        control_layout.addWidget(self.generate_button)

        top_layout.addLayout(control_layout)

        self.chart_label = QLabel("در اینجا نمودار نمایش داده خواهد شد.")
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setStyleSheet("border: 1px solid gray;")
        self.chart_label.setMinimumHeight(400)
        top_layout.addWidget(self.chart_label)

        splitter.addWidget(top_widget)

        # بخش پایینی: نمایش لاگ‌ها
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("لاگ‌های برنامه:"))
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        bottom_layout.addWidget(self.log_text_edit)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([500, 200])  # تنظیم اندازه اولیه

        # تنظیم Handler برای نمایش لاگ در GUI
        gui_handler = GuiLogHandler(self.log_text_edit)
        gui_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        gui_handler.setFormatter(formatter)
        logging.getLogger().addHandler(gui_handler)

    def apply_dark_mode(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        # استایل پیشرفته با QSS
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }
            QComboBox, QPushButton, QLabel, QTextEdit {
                background-color: #2e2e2e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #4a4a4a;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QTextEdit {
                background-color: #1e1e1e;
            }
        """)

    def on_start_chart(self):
        # ذخیره انتخاب‌های کاربر
        self.current_chart_type = self.chart_type_combo.currentText()
        self.current_timeframe = self.timeframe_combo.currentText()
        logging.info(f"Selected Chart: {self.current_chart_type} | Timeframe: {self.current_timeframe}")
        # بلافاصله نمودار را بروزرسانی کنید
        self.update_chart()

    def update_chart(self):
        if self.current_chart_type is None or self.current_timeframe is None:
            return

        # تعیین مقادیر داخلی بر اساس انتخاب کاربر
        if self.current_chart_type == "چارت آب و هوا":
            internal_chart_type = "weather"
        elif self.current_chart_type == "چارت طلا":
            internal_chart_type = "gold"
        elif self.current_chart_type == "چارت دلار":
            internal_chart_type = "dollar"
        else:
            internal_chart_type = "weather"

        if self.current_timeframe == "نمودار 1 ساعته":
            internal_timeframe = "1h"
        elif self.current_timeframe == "نمودار 1 روزه":
            internal_timeframe = "1d"
        elif self.current_timeframe == "نمودار هفتگی":
            internal_timeframe = "1w"
        elif self.current_timeframe == "نمودار ماهانه":
            internal_timeframe = "1m"
        else:
            internal_timeframe = "1d"

        chart_path = generate_chart(chart_type=internal_chart_type, timeframe=internal_timeframe)
        if chart_path and os.path.exists(chart_path):
            pixmap = QPixmap(chart_path)
            if not pixmap.isNull():
                self.chart_label.setPixmap(pixmap.scaled(
                    self.chart_label.width(), self.chart_label.height(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.chart_label.setText("❌ خطا در بارگذاری تصویر نمودار.")
        else:
            self.chart_label.setText("❌ نموداری برای این بازه در دسترس نیست.")

    def start_auto_refresh(self):
        # QTimer برای به‌روزرسانی خودکار نمودار هر 5 ثانیه
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(self.refresh_interval)

# ==================== Telegram Bot Runner ====================
def run_telegram_bot():
    while True:
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            from telegram import KeyboardButton, ReplyKeyboardMarkup  # Import locally if needed
            application = ApplicationBuilder().token(BOT_TOKEN).build()
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("esp32", esp32_command))
            application.add_handler(CommandHandler("esp32_all", esp32_all_command))
            application.add_handler(CommandHandler("chart", chart_command))
            application.add_handler(CommandHandler("admin", admin_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_text))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))
            logging.info("🤖 Telegram bot started successfully. Waiting for commands...")
            application.run_polling()
        except Exception as e:
            logging.error(f"[❌] Telegram bot error: {e}")
            logging.info("⏳ Retrying to connect Telegram Bot in 60 seconds...")
            time.sleep(60)

# ==================== Main Data Logging Loop ====================
def main_data_loop():
    logging.info(Fore.GREEN + "📡 Starting data logging from ESP32...")
    while True:
        try:
            data = fetch_data()
            if data:
                save_to_excel(data)
            else:
                logging.warning(Fore.YELLOW + "[⚠️] No data received in this cycle.")
        except Exception as e:
            logging.error(Fore.RED + f"[❌] Exception in data logging loop: {e}")
        time.sleep(60)

# ==================== Program Entry Point ====================
if __name__ == "__main__":
    BOT_TOKEN = "5086035674:AAGcVY9JrK9CJceRwsHbwYmyhwUIK6WHtRM"
    ADMIN_IDS = [381200758]

    # اجرای نخ‌های ثبت داده و ربات تلگرام به صورت پس‌زمینه
    data_thread = threading.Thread(target=main_data_loop, daemon=True)
    data_thread.start()
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # اجرای رابط گرافیکی PyQt5
    app = QApplication(sys.argv)
    window = ChartWindow()
    window.show()
    sys.exit(app.exec_())
