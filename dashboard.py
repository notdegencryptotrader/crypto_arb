import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Crypto Arbitrage", layout="wide")

st.title("💰 Crypto Arbitrage Finder")

# Sample data
data = {
    'symbol': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    'min_price': [76500, 3500, 140],
    'max_price': [76800, 3520, 142],
    'spread_pct': [0.39, 0.57, 1.42],
}
df = pd.DataFrame(data)

st.dataframe(df)
st.bar_chart(df.set_index('symbol')['spread_pct'])