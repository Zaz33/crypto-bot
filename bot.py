import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

TOKEN = "6977720621:AAEDBKOtQjqkMO0ZAJsR5JsoGBZvzN4FI9I"

CHAT_IDS = set()

async def get_crypto_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,binancecoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    btc = data["bitcoin"]
    eth = data["ethereum"]
    bnb = data["binancecoin"]
    def arrow(change):
        return "📈" if change > 0 else "📉"
    msg = f"""
🕐 *{datetime.now().strftime("%H:%M")} — Crypto գներ*

₿ *Bitcoin (BTC)*
💵 ${btc['usd']:,.2f}
{arrow(btc['usd_24h_change'])} {btc['usd_24h_change']:+.2f}% (24ժ)

Ξ *Ethereum (ETH)*
💵 ${eth['usd']:,.2f}
{arrow(eth['usd_24h_change'])} {eth['usd_24h_change']:+.2f}% (24ժ)

🟡 *BNB*
💵 ${bnb['usd']:,.2f}
{arrow(bnb['usd_24h_change'])} {bnb['usd_24h_change']:+.2f}% (24ժ)
"""
    return msg

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    CHAT_IDS.add(chat_id)
    await update.message.reply_text(
        "✅ Բոտը ակտիվ է։\n\nԱմեն ժամ կուղարկեմ BTC, ETH, BNB գները։\n\n/prices — հիմա տես գները"
    )

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await get_crypto_prices()
    await update.message.reply_text(msg, parse_mode="Markdown")

async def send_hourly(context):
    msg = await get_crypto_prices()
    for chat_id in CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prices", prices))
    app.job_queue.run_repeating(send_hourly, interval=3600, first=10)
    print("Բոտը աշխատում է...")
    app.run_polling()

if __name__ == "__main__":
    main()
