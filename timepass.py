import yfinance as yf 

stock_data = yf.Ticker("AAPL")

print(stock_data.fast_info.keys())
print(stock_data.fast_info["lastPrice"], stock_data.fast_info["currency"])



history_df = stock_data.history()
print(history_df)

data = [
    {'date': str(date.date()), 'close': round(row['Close'], 2)}
    for date, row in history_df.iterrows()
]


print(data)