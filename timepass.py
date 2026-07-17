import yfinance as yf 
import pandas as pd

# stock_data = yf.Ticker("AAPL")

# print(stock_data.fast_info.keys())
# print(stock_data.fast_info["lastPrice"], stock_data.fast_info["currency"])



# history_df = stock_data.history()
# print(history_df)

# data = [
#     {'date': str(date.date()), 'close': round(row['Close'], 2)}
#     for date, row in history_df.iterrows()
# ]


# print(data)


# results = yf.Search("infosys", max_results=15).quotes
# print(results)




# result = yf.Lookup("reliance").get_stock(count=25)


# for symbol, row in result.iterrows() : 
#     print(symbol)
#     print(row)
#     print("\n")




def fetch_stock_name(ticker) : 
    """
    Fetches the full company name for a ticker from yfinance.
    Used once, at Stock creation time — not cached, since it only ever runs a single time per stock (see stock_detail view).
    Returns None if the fetch fails
    """
    try : 
        stock_data = yf.Ticker(ticker)
        return stock_data.info.get('longName')

    except Exception : 
        return None
    
    
    

print(fetch_stock_name("RELIANCE.NS"))