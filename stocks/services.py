import yfinance as yf 
from datetime import timedelta
from django.utils import timezone
from .models import StockPriceCache, StockHistoryCache


# How long cached data is considered "fresh enough" before we refetch.
# Defined here as constants so they're easy to find and tune later.
PRICE_STALE_AFTER = timedelta(minutes=5)
HISTORY_STALE_AFTER = timedelta(hours=1)



#----PUBLIC FUNCTIONS----# 
# Will be used by our views

def get_current_price(stock) : 
    """
    Returns (price, is_stale) for a given Stock.
    is_stale=True means: yfinance failed, so we're serving old cached data.
    Returns (None, None) if there's no data at all (first-ever fetch also failed).
    """
    
    # .filter().first() instead of .get() — .get() raises an error if no row exists, which we don't want here. 
    # .first() just returns None if empty.
    cached = StockPriceCache.objects.filter(stock = stock).first()
    
    # Check Freshness : does a cached row exist AND is it recent enough?
    if cached and (timezone.now() - cached.last_updated) < PRICE_STALE_AFTER : 
        return (cached.price, False)    # fresh enough, no need to hit yfinance at all


    
    # Either no cache exists yet, or it's stale — try fetching fresh data.
    fresh_price = _fetch_price_from_yfinance(stock.ticker)

    # The fetch was successful and we were able to get a fresher price from yfinance 
    # update_or_create: if a StockPriceCache row for this stock exists, update it; otherwise create a new one. 
    # Avoids writing separate "if exists: update, else: create" logic ourselves.
    if fresh_price is not None : 
        StockPriceCache.objects.update_or_create(
            stock = stock, 
            defaults = {'price': fresh_price}
        )
        return (fresh_price, False)




    # The fetch failed. Fall back to the stale cache if we have one
    if cached : 
        return (cached.price, True)     # stale=True tells the view to trigger the pop-up later
    
    
    
    
    # No fresh data AND no cache at all - Genuinely nothing to show 
    return (None, None)











def get_price_history(stock, range_code) : 
    """
    Returns (data, is_stale) for a given (Stock + range) (e.g. '1W', '1M').
    Same stale-fallback pattern as get_current_price, just against StockHistoryCache and keyed by range too.
    """
    
    cached = StockHistoryCache.objects.filter(stock = stock, range = range_code).first()
    
    # Check Freshness : does a cached row exist AND is it recent enough?
    if cached and (timezone.now() - cached.last_updated) < HISTORY_STALE_AFTER : 
        return (cached.data, False)     # fresh enough, no need to hit yfinance at all

    
    
    
    # Either no cache exists yet, or it's stale — try fetching fresh data.
    fresh_data = _fetch_history_from_yfinance(stock.ticker, range_code)
    
    # The fetch was successful and we were able to get a fresher price from yfinance 
    if fresh_data : 
        StockHistoryCache.objects.update_or_create(
            stock = stock, 
            range = range_code, 
            defaults = {'data' : fresh_data}
        )    
        return (fresh_data, False)
    
    
    
    
    
    # The fetch failed. Fall back to the stale cache if we have one
    if cached : 
        return (cached.data, True)



    # No fresh data AND no cache at all - Genuinely nothing to show 
    return (None, None)













#----HELPER FUNCTONS-----
# Will be used to make the API calls
# Leading underscore is a Python convention meaning "internal use only, not meant to be called from outside this file" 
# (not enforced by Python, just a signal to future-you or anyone reading the code).


def _fetch_price_from_yfinance(ticker) : 
    try : 
        stock_data = yf.Ticker(ticker) 
        price = stock_data.fast_info['lastPrice']
        return price 
    
    except Exception : 
        # Catches any faliure
        return None




def _fetch_history_from_yfinance(ticker, range_code) :
    # Maps our range codes to yfinance's expected 'period' argument.
    period_map = {'1W': '5d', '1M': '1mo', '6M': '6mo', '1Y': '1y'}
    
    try :
        stock_data = yf.Ticker(ticker)
        history_df = stock_data.history(period = period_map[range_code])

        # Convert the pandas DataFrame yfinance returns into a plain list
        # of dictionaries — JSONField needs plain Python data (dicts/lists),
        # not pandas objects, which aren't JSON-serializable.
        data = [
            {'date': str(date.date()), 'close': round(float(row['Close']), 2)}
            for date, row in history_df.iterrows()
        ]
        return data
        
    except : 
        return None
     
