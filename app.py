import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Crypto Analyzer Pro", page_icon="💹", layout="wide")

# =========================
# API KEY
# =========================
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
            border: none;
        }
        .stButton>button:hover {
            background-color: #2ea043;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.title("💹 Crypto Analyzer Pro (Coinbase + AI)")
st.caption("Analisis teknikal otomatis (Entry, SL, TP) berdasarkan data candlestick Coinbase")

# =========================
# SELEKSI ASET DAN TIMEFRAME
# =========================
coins = {
    "Bitcoin (BTC/USD)": "BTC-USD",
    "Ethereum (ETH/USD)": "ETH-USD",
    "Solana (SOL/USD)": "SOL-USD",
    "Cardano (ADA/USD)": "ADA-USD",
    "Dogecoin (DOGE/USD)": "DOGE-USD"
}

timeframes = {
    "1 Jam": 3600,
    "4 Jam": 14400,
    "1 Hari": 86400
}

col1, col2 = st.columns([2, 1])
with col1:
    selected_coin = st.selectbox("Pilih aset crypto:", list(coins.keys()))
    symbol = coins[selected_coin]
with col2:
    selected_tf = st.selectbox("Pilih Timeframe:", list(timeframes.keys()))
    granularity = timeframes[selected_tf]

# =========================
# FETCH DATA
# =========================
@st.cache_data(ttl=300)
def get_candlestick_data(symbol="BTC-USD", granularity=3600):
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles?granularity={granularity}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        st.error("Gagal mengambil data candlestick dari Coinbase API.")
        return None
    data = response.json()
    df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.sort_values("time")
    return df

df = get_candlestick_data(symbol, granularity)

# =========================
# TAMPILKAN GRAFIK
# =========================
if df is not None:
    st.subheader(f"Grafik Candlestick — {selected_coin} ({selected_tf})")

    fig = go.Figure(data=[
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color="lime",
            decreasing_line_color="red",
            name="Candlestick"
        )
    ])

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=True,  # bisa digeser manual
        xaxis_title="Waktu",
        yaxis_title="Harga (USD)",
        height=600,
        hovermode="x unified",
        dragmode="pan",  # bisa digeser dengan drag
    )

    st.plotly_chart(fig, use_container_width=True)

    last_price = df["close"].iloc[-1]
    st.info(f"💰 Harga terakhir {selected_coin}: **${last_price:,.2f}**")

    # =========================
    # ANALISIS GPT
    # =========================
    if st.button("📊 Analisis Pasar dengan AI", use_container_width=True):
        with st.spinner("Menganalisis pasar..."):
            # Ambil data ringkas
            last_10 = df.tail(10)[["time", "open", "high", "low", "close"]].to_dict(orient="records")
            prompt = f"""
            Berikut adalah data harga {symbol} timeframe {selected_tf} dari Coinbase:

            {last_10}

            Analisis dengan:
            - Tren harga (bullish, bearish, atau sideways)
            - Entry point (harga masuk ideal)
            - Stop Loss (SL)
            - Take Profit (TP)
            - Berikan reasoning teknikal singkat
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
