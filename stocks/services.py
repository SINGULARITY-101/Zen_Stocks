import yfinance as yf 
from datetime import timedelta
from django.utils import timezone
from .models import StockPriceCache, StockHistoryCache


# How long cached data is considered "fresh enough" before we refetch.
# Defined here as constants so they're easy to find and tune later.
PRICE_STALE_AFTER = timedelta(minutes=5)
HISTORY_STALE_AFTER = timedelta(hours=1)




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
    