import asyncio
import aiohttp
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import pandas as pd
from datetime import datetime
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "6977720621:AAEDBKOtQjqkMO0ZAJsR5JsoGBZvzN4FI9I"
CHAT_IDS = set()

async def get_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin,ethereum,binancecoin", "vs_currencies": "usd", "include_24hr_change": "true"}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params) as r:
            d = await r.json()
    btc = d["bitcoin"]
    eth = d["ethereum"]
    bnb = d["binancecoin"]
    return (f"🕐 Crypto {datetime.now().strftime('%H:%M')}\n\n"
            f"₿ BTC: ${btc['usd']:,.2f} ({btc['usd_24h_change']:+.2f}%)\n"
            f"Ξ ETH: ${eth['usd']:,.2f} ({eth['usd_24h_change']:+.2f}%)\n"
            f"🟡 BNB: ${bnb['usd']:,.2f} ({bnb['usd_24h_change']:+.2f}%)")

async def get_candle_chart(coin_id, symbol):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "2", "interval": "hourly"}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params) as r:
            data = await r.json()

    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open", "close"]].max(axis=1) * 1.002
    df["low"] = df[["open", "close"]].min(axis=1) * 0.998
    df = df[["open", "high", "low", "close"]].tail(48)

    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit')
    style = mpf.make_mpf_style(
        marketcolors=mc,
        facecolor='#1a1a2e',
        edgecolor='#2a2a4a',
        figcolor='#1a1a2e',
        gridcolor='#2a2a4a',
        gridstyle='--',
        rc={'text.color': 'white', 'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'}
    )

    buf = BytesIO()
    mpf.plot(
        df,
        type='candle',
        style=style,
        title=f'\n{symbol} — 1ժ մոմեր (48ժ)',
        ylabel='Գին (USD)',
        figsize=(12, 7),
        savefig=dict(fname=buf, format='png', dpi=100, bbox_inches='tight'),
        mav=(7, 25),
        mavcolors=['#ff9f43', '#a29bfe']
    )
    buf.seek(0)
    return buf

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df.tail(48)

    mc = mpf.make_marketcolors(
        up='#26a69a',
        down='#ef5350',
        edge='inherit',
        wick='inherit',
        volume='in',
    )
    style = mpf.make_mpf_style(
        marketcolors=mc,
        facecolor='#1a1a2e',
        edgecolor='#2a2a4a',
        figcolor='#1a1a2e',
        gridcolor='#2a2a4a',
        gridstyle='--',
        y_on_right=False,
        rc={'font.size': 10, 'text.color': 'white', 'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'}
    )

    buf = BytesIO()
    mpf.plot(
        df,
        type='candle',
        style=style,
        title=f'\n{symbol} — 1ժ մոմեր (48ժ)',
        ylabel='Գին (USD)',
        figsize=(12, 7),
        savefig=dict(fname=buf, format='png', dpi=100, bbox_inches='tight'),
        mav=(7, 25),
        mavcolors=['#ff9f43', '#a29bfe']
    )
    buf.seek(0)
    return buf

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(u.effective_chat.id)
    await u.message.reply_text(
        "✅ Բոտը ակտիվ է\n\n"
        "/prices — գներ\n"
        "/btc — BTC candlestick\n"
        "/eth — ETH candlestick\n"
        "/bnb — BNB candlestick"
    )

async def prices(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text(await get_prices())

async def btc(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("⏳ Կառուցում եմ BTC գրաֆիկը...")
    buf = await get_candle_chart("bitcoin", "BTC")
    await u.message.reply_photo(photo=buf, caption="₿ Bitcoin — Candlestick 1ժ")

async def eth(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("⏳ Կառուցում եմ ETH գրաֆիկը...")
    buf = await get_candle_chart("ethereum", "ETH")
    await u.message.reply_photo(photo=buf, caption="Ξ Ethereum — Candlestick 1ժ")

async def bnb(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("⏳ Կառուցում եմ BNB գրաֆիկը...")
    buf = await get_candle_chart("binancecoin", "BNB")
    await u.message.reply_photo(photo=buf, caption="🟡 BNB — Candlestick 1ժ")

async def hourly(c):
    msg = await get_prices()
    for cid in CHAT_IDS:
        await c.bot.send_message(chat_id=cid, text=msg)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prices", prices))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("eth", eth))
    app.add_handler(CommandHandler("bnb", bnb))
    app.job_queue.run_repeating(hourly, interval=3600, first=10)
    print("Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()