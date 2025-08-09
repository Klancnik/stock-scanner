import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Define a list of stock tickers to scan (small set for prototyping)
tickers = ["AAPL", "MSFT", "TSLA", "JPM", "WMT", "PG", "XOM", "PFE"]

# Function to fetch implied volatility from options data
def get_implied_volatility(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Get options chain for the nearest expiration date
        expirations = stock.options
        if not expirations:
            return None
        option_chain = stock.option_chain(expirations[0])
        
        # Average IV from at-the-money (ATM) calls and puts
        calls = option_chain.calls
        puts = option_chain.puts
        if calls.empty or puts.empty:
            return None
            
        # Filter for ATM options (closest to current stock price)
        stock_price = stock.history(period="1d")["Close"].iloc[-1]
        calls_atm = calls.iloc[(calls["strike"] - stock_price).abs().argsort()[:1]]
        puts_atm = puts.iloc[(puts["strike"] - stock_price).abs().argsort()[:1]]
        
        # Return average IV
        iv = (calls_atm["impliedVolatility"].mean() + puts_atm["impliedVolatility"].mean()) / 2
        return iv
    except Exception as e:
        print(f"Error fetching IV for {ticker}: {e}")
        return None

# Main function to scan stocks and filter for low IV
def scan_low_iv_stocks(tickers, percentile=20):
    iv_data = []
    
    # Fetch IV for each ticker
    for ticker in tickers:
        iv = get_implied_volatility(ticker)
        if iv is not None:
            iv_data.append({"Ticker": ticker, "Implied Volatility": iv})
    
    # Convert to DataFrame
    df = pd.DataFrame(iv_data)
    if df.empty:
        print("No valid IV data found.")
        return None
    
    # Calculate the IV threshold (e.g., 20th percentile)
    iv_threshold = np.percentile(df["Implied Volatility"], percentile)
    
    # Filter for stocks with IV below threshold
    low_iv_stocks = df[df["Implied Volatility"] <= iv_threshold]
    
    # Sort by IV (ascending)
    low_iv_stocks = low_iv_stocks.sort_values(by="Implied Volatility")
    
    return low_iv_stocks

# Run the scanner
if __name__ == "__main__":
    print(f"Scanning stocks for low implied volatility on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    low_iv_df = scan_low_iv_stocks(tickers)
    
    if low_iv_df is not None and not low_iv_df.empty:
        print("\nStocks with low implied volatility (below 20th percentile):")
        print(low_iv_df)
    else:
        print("No stocks found with low implied volatility.")