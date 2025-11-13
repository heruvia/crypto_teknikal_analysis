import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Crypto Market Analyzer", page_icon="💹", layout="wide")

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "ISI_API_KEY_KAMU_DI_SINI")
BITPANDA_TICKER_URL = "https://api.bitpanda.com/v1/ticker"
BITPANDA_CANDLE_URL = "https://api.exchange.bitpanda.com/public/v1/candlesticks"

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# STYLE
# =========================
st.markdown("""
<style>
body {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Inter', sans-serif;
}
.main {
    background-color: #0d1117;
    color: #e6edf3;
}
h1, h2, h3 {
    color: #f0f6fc;
}
.card {
    background: linear-gradient(145deg, #161b22, #1e2229);
    padding: 1.8rem;
    border-radius: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
    margin-bottom: 2rem;
}
.price {
    font-size: 1.8rem;
    font-weight: 700;
    color: #39d353;
}
.meta {
    color: #8b949e;
    font-size: 0.9rem;
}
.btn-analyze {
    background-color: #238636 !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
.btn-analyze:hover {
    background-color: #2ea043 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<h1 style='text-align:center;'>💹 Crypto Market Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e;'>Harga real-time, grafik candlestick, dan analisis otomatis berbasis AI</p>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# =========================
# FETCH DATA FUNCTIONS
# =========================
@st.cache_data(ttl=300)
def get_tickers():
    try:
        res = requests.get(BITPANDA_TICKER_URL, timeout=10)
        return res.json()
    except Exception as e:
        st.error(f"Gagal mengambil data harga: {e}")
        return None

@st.cache_data(ttl=300)
def get_candles(symbol="BTC_EUR", unit="HOUR", period=1):
    try:
        url = f"{BITPANDA_CANDLE_URL}?instrument_code={symbol}&unit={unit}&period={period}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception as e:
        st.warning(f"Gagal ambil data candlestick: {e}")
    return []

# =========================
# MAIN CONTENT
# =========================
data = get_tickers()

if data:
    coins = list(data.keys())
    selected_coin = st.selectbox("Pilih aset crypto:", coins, index=0)
    coin_data = data[selected_coin]
    eur_price = float(coin_data.get("EUR", 0))
    usd_price = float(coin_data.get("USD", 0))

    st.markdown(f"""
        <div class="card">
            <h2>{selected_coin}</h2>
            <div class="price">€{eur_price:,.2f} / ${usd_price:,.2f}</div>
            <div class="meta">Sumber: Bitpanda | Diperbarui: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)

    # =========================
    # CANDLESTICK CHART
    # =========================
    st.subheader(f"📊 Grafik Candlestick — {selected_coin}/EUR (24 Jam Terakhir)")
    with st.spinner("Mengambil data grafik..."):
        candles = get_candles(f"{selected_coin}_EUR", "HOUR", 1)

        if candles:
            df = pd.DataFrame(candles)
            df["time"] = pd.to_datetime(df["time"])
            df = df.sort_values("time")
            fig = go.Figure(data=[go.Candlestick(
                x=df["time"],
                open=df["open"].astype(float),
                high=df["high"].astype(float),
                low=df["low"].astype(float),
                close=df["close"].astype(float),
                increasing_line_color="#2ea043",
                decreasing_line_color="#f85149"
            )])
            fig.update_layout(
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                height=400,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Tidak ada data candlestick untuk ditampilkan.")

    # =========================
    # ANALISIS GPT
    # =========================
    if st.button("🤖 Analisis Pasar Sekarang", type="primary", use_container_width=True):
        with st.spinner("Menganalisis data pasar..."):
            prompt = f"""
            Berikut adalah data harga crypto {selected_coin}:

            - Harga EUR: €{eur_price:,.2f}
            - Harga USD: ${usd_price:,.2f}
            - Data historis 24 jam terakhir (candlestick)

            Berdasarkan data ini:
            1. Jelaskan sentimen pasar (bullish, bearish, atau sideways)
            2. Tentukan level entry yang ideal
            3. Tentukan Stop Loss (SL) dan Take Profit (TP)
            4. Tulis analisis secara profesional, rapi, dan ringkas
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": prompt}],
                )
                analysis = response.choices[0].message.content.strip()
                st.success(analysis)
            except Exception as e:
                st.error(f"Gagal menganalisis: {e}")
else:
    st.error("Tidak dapat memuat data harga dari Bitpanda.")
