import requests
import xmltodict 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from datetime import datetime, timezone
import os 
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

API_URL = "https://meridian.centrum-air.com/meridian-server/rest/named-queries/timetable?left=3&right=1"
HEADERS = {"Authorization" : "Basic YXZ0cmElMTpuZkh0OTM4JmQ="}

TRANSLATIONS = {
    "en": {
        "start": "Hello! I can show you live Meridian flights.\n"
                 "Try commands:\n"
                 "• /flight <i>305</i>\n"
                 "• /arrivals\n"
                 "• /departures\n\n"
                 "Change language: /lang uz | /lang ru | /lang en",

        "usage_flight": "Usage: /flight <i>305</i>",
        "flight_not_found": "Flight {flight_no} not found.",
        "upcoming_arrivals": "Upcoming Arrivals to TAS",
        "upcoming_departures": "Upcoming Departures from TAS",
        "no_arrivals": "No arrivals found.",
        "no_departures": "No departures found.",
        "planned": "Planned",
        "estimated": "Est",
        "status": "Status",
        "aircraft": "Aircraft",
        "lang_set": "Language set to English",
        "lang_menu": "Choose language:",
    },
    "ru": {
        "start": "Привет! Я показываю рейсы Meridian в реальном времени.\n"
                 "Команды:\n"
                 "• /flight <i>305</i>\n"
                 "• /arrivals\n"
                 "• /departures\n\n"
                 "Сменить язык: /lang uz | /lang ru | /lang en",

        "usage_flight": "Использование: /flight <i>305</i>",
        "flight_not_found": "Рейс {flight_no} не найден.",
        "upcoming_arrivals": "Прилёты в TAS",
        "upcoming_departures": "Вылеты из TAS",
        "no_arrivals": "Прилётов нет.",
        "no_departures": "Вылетов нет.",
        "planned": "План",
        "estimated": "Ожид.",
        "status": "Статус",
        "aircraft": "ВС",
        "lang_set": "Язык изменён на русский",
        "lang_menu": "Выберите язык:",
    },
    "uz": {
        "start": "Salom! Men Meridian reyslarini real vaqtda ko‘rsata olaman.\n"
                 "Buyruqlar:\n"
                 "• /flight <i>305</i>\n"
                 "• /arrivals\n"
                 "• /departures\n\n"
                 "Tilni o‘zgartirish: /lang uz | /lang ru | /lang en",

        "usage_flight": "Foydalanish: /flight <i>305</i>",
        "flight_not_found": "Parvoz {flight_no} topilmadi.",
        "upcoming_arrivals": "TAS ga keladigan reyslar",
        "upcoming_departures": "TAS dan uchadigan reyslar",
        "no_arrivals": "Keladigan reys yo‘q.",
        "no_departures": "Uchadigan reys yo‘q.",
        "planned": "Reja",
        "estimated": "Taxmin",
        "status": "Holati",
        "aircraft": "Samolyot",
        "lang_set": "Til o‘zbek tiliga o‘zgartirildi",
        "lang_menu": "Tilni tanlang:",
    }
}

def t(user_data, key, **kwargs):
    lang = user_data.get("lang", "ru")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("O‘zbek", callback_data="lang_uz"),
            InlineKeyboardButton("Русский", callback_data="lang_ru"),
            InlineKeyboardButton("English", callback_data="lang_en"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t(context.user_data, "lang_menu"), reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.user_data["lang"] = lang
        await query.edit_message_text(t(context.user_data, "lang_set"))



def parse_date_safe(date_str: str):
    """Parse date like '08.11.2025 14:10' → datetime, or None."""
    if not date_str or not date_str.strip():
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%d.%m.%Y %H:%M")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t(context.user_data, "start"), parse_mode="HTML")

def fetch_flights():
    """Fetch and parse XML from API. """
    resp = requests.get(API_URL, headers=HEADERS, timeout=30)
    data = xmltodict.parse(resp.text)
    return data.get("FLIGHT_TYPE", {}).get("FLIGHT", [])


def find_flight_by_number(flights, flight_no):
    for f in flights:
        if f.get("FLIGHT_NO") == flight_no:
            return f
    return None


async def flight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(t(context.user_data, "usage_flight"), parse_mode="HTML")
        return
    
    flight_no = context.args[0]
    flights = fetch_flights()
    flight = find_flight_by_number(flights, flight_no)

    if not flight:
        await update.message.reply_text(t(context.user_data, "flight_not_found", flight_no=flight_no))
        return

    leg = flight["LEG"]
    text = (
        f"✈️ <b>{flight['CARRIER']} {flight['FLIGHT_NO']}</b>\n"
        f"{leg['ORIGIN_NAME_TR']} ({leg['ORIGIN_IATA']}) → {leg['DESTINATION_NAME_TR']} ({leg['DESTINATION_IATA']})\n\n"
        f"<b>{t(context.user_data, 'planned')}:</b> {leg['DEPARTURE_PLAN_LOCAL']} → {leg['ARRIVAL_PLAN_LOCAL']}\n"
        f"<b>{t(context.user_data, 'estimated')}:</b> {leg['DEPARTURE_EST_LOCAL']} → {leg['ARRIVAL_EST_LOCAL']}\n"
        f"<b>Actual:</b> {leg['DEPARTURE_FACT_LOCAL']} → {leg['ARRIVAL_FACT_LOCAL']}\n\n"
        f"{t(context.user_data, 'status')}: {leg['STATUS']} | {t(context.user_data, 'aircraft')}: {leg['NAME_TYP']} ({leg['BORT']})"
    )
    await update.message.reply_text(text, parse_mode="HTML")



async def arrivals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flights = fetch_flights()
    now = datetime.now(timezone.utc)
    # arrivals → flights landing at TAS (Tashkent)
    arrivals = []
    for f in flights: 
        legs = f.get("LEG")
        if isinstance(legs, list):
            leg = legs[-1]
        else:
            leg = legs

        if leg and leg.get("DESTINATION_IATA") == "TAS":
            time = parse_date_safe(leg.get("ARRIVAL_PLAN_UTC")) or parse_date_safe(leg.get("ARRIVAL_EST_UTC"))
            if time and time >= now:
                arrivals.append({**f, "LEG": leg})

    # sort by planned arrival
    arrivals = sorted(arrivals, key=lambda f: parse_date_safe(f["LEG"].get("ARRIVAL_EST_LOCAL", "")) or datetime.max)[:5]

    text = f"🛬 <b>{t(context.user_data, 'upcoming_arrivals')}</b>\n\n"
    for f in arrivals:
        leg = f["LEG"]
        text += (
            f"{f['CARRIER']} {f['FLIGHT_NO']}  "
            f"{leg['ORIGIN_IATA']} → {leg['DESTINATION_IATA']}\n"
            f"Planned: {leg['ARRIVAL_PLAN_LOCAL']}\n"
            f"Est: {leg['ARRIVAL_EST_LOCAL']}\n\n"
        )

    await update.message.reply_html(text.strip() or "No arrivals found.")



async def departures_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flights = fetch_flights()
    now = datetime.now(timezone.utc)

    departures = []
    for f in flights:
        legs = f.get("LEG")
        # if multiple legs, take the first one (departure)
        if isinstance(legs, list):
            leg = legs[0]
        else:
            leg = legs

        if leg and leg.get("ORIGIN_IATA") == "TAS":
            time = parse_date_safe(leg.get("DEPARTURE_PLAN_UTC")) or parse_date_safe(leg.get("DEPARTURE_EST_UTC"))
            if time and time >= now:
                departures.append({**f, "LEG": leg})

    departures = sorted(departures, key=lambda f: parse_date_safe(f["LEG"].get("DEPARTURE_EST_LOCAL", "")) or datetime.max)[:5]

    text = f"🛫 <b>{t(context.user_data, 'upcoming_departures')}</b>\n\n"
    for f in departures:
        leg = f["LEG"]
        text += (
            f"{f['CARRIER']} {f['FLIGHT_NO']}  "
            f"{leg['ORIGIN_IATA']} → {leg['DESTINATION_IATA']}\n"
            f"Planned: {leg.get('DEPARTURE_PLAN_LOCAL')}\n"
            f"Est: {leg.get('DEPARTURE_EST_LOCAL')}\n\n"
        )

    await update.message.reply_html(text.strip() or "No departures found.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("flight", flight_command))
    app.add_handler(CommandHandler("arrivals", arrivals_command))
    app.add_handler(CommandHandler("departures", departures_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Bot is running...")
    app.run_polling()



if __name__ == "__main__":
    main()
