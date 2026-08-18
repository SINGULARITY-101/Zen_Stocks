# Context processors run automatically on every template render, and their 
# returned dict gets merged into that render's context — no view needs to
# pass this data manually. Registered in settings.py -> TEMPLATES -> OPTIONS.

# Used for data that needs to be present in every page 
# NOTE : Has a huge performance cost. Ensure you are not running huge operations in the context processor 

from .models import WatchlistItem
from .services import get_current_price






def sidebar_context(request) : 
    """
    Injects 'sidebar_watchlist' into every template's context.
    Used by sidebar.html (included in base.html on every page).
    """
    
    # Anonymous users have no watchlist to query — return an empty list.
    # sidebar.html will check this + user.is_authenticated to decide
    # whether to show real rows or the "Log in to view" prompt
    if not request.user.is_authenticated : 
        return {'sidebar_watchlist': []}
    
    watchlist_data = []
    
    
    
    # select_related is a very important performance optimization 
    # Without it, looping over watchlist.all() and accessing item.stock inside would have triggered a separate DB query per item 
    
    # Lets say there were 5 stocks on the watchlist
    # That would result in : 1 DB query for the watchlist + 5 DB queries for each stock
    
    # select_related tells django to fetch the related Stock row in the same query via a SQL join 
    # This would result in 1 DB query REGARDLESS of watchlist size
    
    for item in WatchlistItem.objects.filter(user = request.user).select_related('stock') : 
        price, previous_close, is_stale = get_current_price(item.stock)
        
        # Guard Against None (No Data yet) and 0 (would divide by zero)
        percent_change = None 
        if price is not None and previous_close : 
            percent_change = ((price - previous_close) / previous_close) * 100

        watchlist_data.append({
            'stock': item.stock,
            'price': price,
            'percent_change': percent_change,
            'is_stale': is_stale,
        })

        return {'sidebar_watchlist': watchlist_data}
        