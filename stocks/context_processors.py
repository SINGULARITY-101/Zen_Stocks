# Context processors run automatically on every template render, and their 
# returned dict gets merged into that render's context — no view needs to
# pass this data manually. Registered in settings.py -> TEMPLATES -> OPTIONS.

# Used for data that needs to be present in every page 
# NOTE : Has a huge performance cost. Ensure you are not running huge operations in the context processor 

from .models import WatchlistItem
from .services import get_current_price, get_price_history, search_stocks




SPARKLINE_WIDTH = 60
SPARKLINE_HEIGHT = 20 





def _build_sparkline_points(closes) : 
    """
    Converts a list of closing prices into an SVG <polyline points="..."> string, scaled to fit a SPARKLINE_WIDTH x SPARKLINE_HEIGHT box.
    Returns None if there isn't enough data to draw a line (need at least 2 points).
    """
    if not closes or len(closes) < 2 : 
        return None 

    min_price = min(closes)
    max_price = max(closes)
    price_range = max_price - min_price


    # A flat-line stock (no movement all week) would divide by zero below.
    # Fall back to 1 so it draws as a flat horizontal line instead of crashing.
    if price_range == 0 : 
        price_range = 1 
    
    n = len(closes)
    points = []
    
    
    for (i, price) in enumerate(closes) : 
        # x: spread points evenly left-to-right across the box
        x = (i / (n-1)) * SPARKLINE_WIDTH

        # y: SVG's y-axis grows DOWNWARD (0 = top), opposite of price intuition
        # So we invert: highest price -> y=0, lowest price -> y=SPARKLINE_HEIGHT.
        y = SPARKLINE_HEIGHT - ((price - min_price) / price_range) * SPARKLINE_HEIGHT
        
        points.append(f"{x:.1f},{y:.1f}")
    
    
    return " ".join(points)



        
        
    
           
    






def sidebar_context(request) : 
    """
    Injects sidebar data into every template's context : 
    - Search Results 
    - All watchlist items
    - Sparklines for the watchlist items
    
    Used by sidebar.html (included in base.html on every page).
    """
    
    
    # ---- SEARCH ----
    # Reads ?q= from whatever URL the sidebar form was submitted against.
    # Available regardless of login state — browsing/searching needs no account.
    query = request.GET.get('q', '').strip()
    search_results = search_stocks(query) if query else []
    
    
    
    
    # ---- WATCHLIST ----
    # Anonymous users have no watchlist to query — return search data only,empty watchlist. 
    # sidebar.html shows "Log in to view" for the dropdowns.
    if not request.user.is_authenticated : 
        return {
            'sidebar_search_query': query,
            'sidebar_search_results': search_results,
            'sidebar_watchlist': [],
        }
    
    
    
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
        
        
        # ---- SPARKLINES ----
        # For sparklines in the watchlist
        # Fetches the historical data -> Sends it to the helper function which generates coordinates for the SVG polyline
        history, history_is_stale = get_price_history(item.stock, '1W')
        sparkline_points = None
        if history:
            closes = [entry['close'] for entry in history]
            sparkline_points = _build_sparkline_points(closes)

        

        watchlist_data.append({
            'stock': item.stock,
            'price': price,
            'percent_change': percent_change,
            'is_stale': is_stale,
            'sparkline_points': sparkline_points,
        })

    
    return {
        'sidebar_search_query': query,
        'sidebar_search_results': search_results,
        'sidebar_watchlist': watchlist_data,
    }
        