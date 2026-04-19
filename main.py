from fastapi import FastAPI, Request
from anthropic import Anthropic
import httpx, os

app = FastAPI()
client = Anthropic()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SYSTEM_PROMPT = """You are an options trading assistant. 
The trader buys directional calls/puts, 5-7 DTE, on stocks, SPX, NDX, SPY, QQQ.
They use an ORB (opening range breakout) retest strategy.

When given a signal respond in this format:

DECISION: BUY CALL / BUY PUT / SKIP
STRIKE: ATM or 1 OTM (based on ATR%)
EXPIRY: nearest Friday 5-7 days out
CONFIDENCE: Low / Medium / High
REASON: 2 sentences max
STOP: where to exit if wrong"""

async def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as http:
        await http.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    symbol = data.get("symbol", "?")
    signal = data.get("signal", "?")
    price  = data.get("price", "?")
    rsi    = data.get("rsi", "?")
    atr    = data.get("atrPct", "?")

    prompt = f"""New ORB retest signal:
Symbol: {symbol}
Signal: {signal}
Price: ${price}
RSI: {rsi}
ATR%: {atr}%
ORB High: {data.get('orbHigh')}
ORB Low: {data.get('orbLow')}
Time: {data.get('time')}

Give me my options trade."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    analysis = response.content[0].text
    message = f"🔔 {symbol} {signal} SIGNAL\n\n{analysis}"
    
    await send_telegram(message)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "running"}
