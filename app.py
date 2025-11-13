import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Crypto Analyzer", page_icon="💹", layout="wide")

# ======== API KEYS ========
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "ISI_API_KEY_KAMU_DI_SINI")
client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# STYLE
# =========================
st.markdown("""
    <style>
        body {background-color: #0d1117; color: #e6edf3;}
        .main {background-color: #0d1117;}
        h1, h2, h3 {color: #f0f6fc;}
        .stButton>button {
            background-color: #238636;
            color: white;
            border-radius: 8px;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #2ea043;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.title("💹 Crypto Analyzer (Coinbase + GPT)")
st.caption("Dapatkan analisis Entry, SL, dan TP berdasarkan data candlestick Coinbase")

# =========================
# PILIH ASET
# =========================
coins = {
    "Bitcoin (BTC/USD)": "BTC-USD",
    "Ethereum (ETH/USD)": "ETH-USD",
    "Solana (SOL/USD)": "SOL-USD",
    "Cardano (ADA/USD)": "ADA-USD",
    "Dogecoin (DOGE/USD)": "DOGE-USD"
}

selected_coin = st.selectbox("Pilih aset crypto:", list(coins.keys()))
symbol = coins[selected_coin]

# =========================
# FETCH DATA
# =========================
@st.cache_data(ttl=300)
def get_coinbase_candles(symbol="BTC-USD", granularity=3600):
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles?granularity={granularity}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        st.error("Gagal mengambil data dari Coinbase API.")
        return None
    data = response.json()
    # Coinbase data format: [time, low, high, open, close, volume]
    df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("time")
    return df

df = get_coinbase_candles(symbol)

if df is not None:
    st.subheader(f"Grafik Candlestick: {selected_coin}")
    fig = go.Figure(data=[go.Candlestick(
        x=df["time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    last_price = df["close"].iloc[-1]
    st.info(f"💰 Harga terakhir {selected_coin}: **${last_price:,.2f}**")

    # =========================
    # ANALISIS GPT
    # =========================
    if st.button("📊 Analisis Pasar dengan GPT", use_container_width=True):
        with st.spinner("Menganalisis pasar..."):

            # Ambil data ringkas untuk GPT
            last_5 = df.tail(5)[["time", "open", "high", "low", "close"]].to_dict(orient="records")
            prompt = f"""
            Berikut adalah data harga {symbol} dari Coinbase (candlestick terakhir 5 jam):

            {last_5}

            Berdasarkan data ini:
            - Analisis apakah tren harga cenderung bullish, bearish, atau sideways.
            - Berikan rekomendasi:
              * Entry point (harga masuk)
              * Stop Loss (SL)
              * Take Profit (TP)
            - Jelaskan dengan singkat dan profesional.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis = response.choices[0].message.content.strip()
                st.success(analysis)
            except Exception as e:
                st.error(f"❌ Gagal menganalisis: {e}")

else:
    st.error("Tidak ada data candlestick tersedia.")

