import pandas as pd
import yfinance as yf
import talib
import time
from datetime import datetime
import requests
import streamlit as st

# === Settings ===
STOCK_LIST = ['AAPL', 'TSLA', 'INFY.NS', 'RELIANCE.NS']  # US + NSE stocks
TIMEFRAME = '5m'
PERIOD = '1d'
TELEGRAM_BOT_TOKEN = '7424007039:AAG62YomUNo2ipomDJsUk-nlDCDEiky6IS0'
TELEGRAM_CHAT_ID = 'charts_pattern_bot'

# === Alert via Telegram ===
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(url, data=payload)

# === Pattern Detection ===
def detect_double_top_bottom(df):
    close = df['Close'].values
    peaks = talib.MAX(close, timeperiod=5)
    troughs = talib.MIN(close, timeperiod=5)
    patterns = []
    for i in range(5, len(close)):
        if abs(close[i] - peaks[i-5]) < 0.5:
            patterns.append((df.index[i], 'Potential Double Top'))
        elif abs(close[i] - troughs[i-5]) < 0.5:
            patterns.append((df.index[i], 'Potential Double Bottom'))
    return patterns

def detect_head_shoulders(df):
    patterns = []
    for i in range(2, len(df)-2):
        ls = df['High'][i-2] < df['High'][i-1] < df['High'][i]
        rs = df['High'][i] > df['High'][i+1] > df['High'][i+2]
        if ls and rs:
            patterns.append((df.index[i], 'Potential Head and Shoulders'))
    return patterns

def detect_flag_pennant(df):
    patterns = []
    for i in range(20, len(df)):
        recent = df['Close'][i-20:i]
        slope = (recent.iloc[-1] - recent.iloc[0]) / 20
        pullback = recent.max() - recent.min()
        if slope > 0 and pullback / recent.iloc[0] < 0.03:
            patterns.append((df.index[i], 'Potential Bullish Flag / Pennant'))
        elif slope < 0 and pullback / recent.iloc[0] < 0.03:
            patterns.append((df.index[i], 'Potential Bearish Flag / Pennant'))
    return patterns

# === Streamlit Dashboard ===
def display_dashboard(stock_data):
    st.title("Real-Time Chart Pattern Detection")
    for stock, patterns in stock_data.items():
        st.subheader(f"{stock}")
        if patterns:
            for timestamp, pattern in patterns:
                st.write(f"{timestamp} - {pattern}")
        else:
            st.write("No significant pattern detected.")

# === Main Loop ===
def monitor_stocks():
    all_patterns = {}
    for stock in STOCK_LIST:
        try:
            data = yf.download(stock, interval=TIMEFRAME, period=PERIOD)
            if data.empty:
                continue
            dt_patterns = detect_double_top_bottom(data)
            hs_patterns = detect_head_shoulders(data)
            flag_patterns = detect_flag_pennant(data)
            combined = dt_patterns + hs_patterns + flag_patterns
            all_patterns[stock] = combined
            for timestamp, pattern in combined:
                alert_message = f"[{timestamp}] {stock}: {pattern}"
                send_telegram_alert(alert_message)
                print(alert_message)
        except Exception as e:
            print(f"Error fetching data for {stock}: {e}")
    return all_patterns

if __name__ == "__main__":
    print(f"Pattern Detection Bot Started at {datetime.now()}")
    result = monitor_stocks()
    display_dashboard(result)
    while True:
        time.sleep(300)  # 5 minutes interval
        result = monitor_stocks()
        display_dashboard(result)

