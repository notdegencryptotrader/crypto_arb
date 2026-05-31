# ============================================
# FETCH FUTURES FUNDING RATE DATA
# Run this script to update futures arbitrage data
# ============================================

import requests
import pandas as pd
import json
import os
import time
from datetime import datetime

API_KEY = "f546c40eed4a45b49ea8e5811c3bc016"

headers = {
    "accept": "application/json",
    "CG-API-KEY": API_KEY
}

# Create folders
os.makedirs("data/futures/raw_json", exist_ok=True)
os.makedirs("data/futures/processed_csv", exist_ok=True)
os.makedirs("data/futures/analysis", exist_ok=True)

print("=" * 60)
print("FETCHING FUTURES FUNDING RATE ARBITRAGE DATA")
print("=" * 60)

# Step 1: Get all futures market data
url = "https://open-api-v4.coinglass.com/api/futures/pairs-markets?symbol=BTC"
print("\n📡 Fetching futures market data...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Found {len(data.get('data', []))} BTC futures markets")
    
    # Save raw JSON
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%H%M%S")
    json_filename = f"data/futures/raw_json/futures_market_data_{current_date}_{current_time}.json"
    with open(json_filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"💾 JSON saved: {json_filename}")
    
    # Create DataFrame
    df = pd.DataFrame(data['data'])
    df['fetch_timestamp'] = datetime.now()
    
    # Save CSV
    csv_filename = f"data/futures/processed_csv/futures_market_data_{current_date}_{current_time}.csv"
    df.to_csv(csv_filename, index=False)
    print(f"💾 CSV saved: {csv_filename}")
    
    # Calculate arbitrage opportunities
    # Group by symbol to find funding rate discrepancies
    df['funding_rate_pct'] = df['funding_rate'] * 100
    
    discrepancy_df = df.groupby('symbol').agg(
        min_funding_rate=('funding_rate_pct', 'min'),
        max_funding_rate=('funding_rate_pct', 'max'),
        avg_funding_rate=('funding_rate_pct', 'mean'),
        exchange_count=('exchange_name', 'nunique'),
        avg_price=('current_price', 'mean'),
        total_volume=('volume_usd', 'sum'),
        exchanges=('exchange_name', lambda x: list(x))
    ).reset_index()
    
    discrepancy_df['funding_spread'] = discrepancy_df['max_funding_rate'] - discrepancy_df['min_funding_rate']
    discrepancy_df = discrepancy_df.sort_values('funding_spread', ascending=False)
    
    # Save discrepancies
    disc_filename = f"data/futures/analysis/funding_discrepancies_{current_date}_{current_time}.csv"
    discrepancy_df.to_csv(disc_filename, index=False)
    print(f"💾 Funding discrepancies saved: {disc_filename}")
    
    # Find best arbitrage opportunities
    arbitrage_list = []
    for symbol in discrepancy_df.head(20)['symbol'].tolist():
        symbol_data = df[df['symbol'] == symbol]
        if len(symbol_data) >= 2:
            best_short = symbol_data.loc[symbol_data['funding_rate'].idxmax()]
            best_long = symbol_data.loc[symbol_data['funding_rate'].idxmin()]
            arbitrage_list.append({
                'symbol': symbol,
                'short_exchange': best_short['exchange_name'],
                'short_funding_rate': best_short['funding_rate_pct'],
                'short_price': best_short['current_price'],
                'short_volume': best_short['volume_usd'],
                'long_exchange': best_long['exchange_name'],
                'long_funding_rate': best_long['funding_rate_pct'],
                'long_price': best_long['current_price'],
                'long_volume': best_long['volume_usd'],
                'funding_spread': (best_short['funding_rate'] - best_long['funding_rate']) * 100,
                'annualized_apr': (best_short['funding_rate'] - best_long['funding_rate']) * 3 * 365 * 100
            })
    
    arbitrage_df = pd.DataFrame(arbitrage_list)
    arb_filename = f"data/futures/analysis/arbitrage_opportunities_{current_date}_{current_time}.csv"
    arbitrage_df.to_csv(arb_filename, index=False)
    print(f"💾 Arbitrage opportunities saved: {arb_filename}")
    
    # Display top opportunities
    print("\n" + "=" * 60)
    print("🏆 TOP ARBITRAGE OPPORTUNITIES")
    print("=" * 60)
    print(arbitrage_df.head(10)[['symbol', 'short_exchange', 'short_funding_rate', 
                                  'long_exchange', 'long_funding_rate', 'funding_spread', 'annualized_apr']].to_string(index=False))
    
else:
    print(f"❌ API Error: {response.status_code}")

print("\n✅ COMPLETE!")