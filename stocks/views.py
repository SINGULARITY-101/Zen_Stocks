from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login  # logs a user in by attaching them to the session
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse


from .forms import SignUpForm  # the form we just built
from .models import Stock, StockHistoryCache, WatchlistItem
from .services import get_current_price, get_price_history, fetch_stock_name # all api calls exist here






# Create your views here.

"""
signup_view
- Django does not ship with a singup view because "how to create a user" varies per project
- A simple function-based view is the standard choice because we don't need the extra structure a class-based view brings

What the view needs to do? 
    * If it's a GET request → show a blank form
    * If it's a POST request → validate the submitted data, and either:
        - Save the new user + log them in automatically, or
        - Re-show the form with errors

"""


def signup_view(request):
    # request.method tells us whether the user is loading the page (GET)
    # or submitting the form they filled out (POST)
    if request.method == 'POST':
        # Bind the submitted data to the form so it can be validated
        form = SignUpForm(request.POST)

        # is_valid() runs all validation: required fields, email format,
        # password match, password strength — all inherited from UserCreationForm
        if form.is_valid():
            # save() creates the User row AND hashes the password correctly —
            # this is the method we inherited for free by subclassing UserCreationForm
            user = form.save()

            # Automatically log the new user in — without this line, they'd have
            # to manually go log in right after signing up. Better UX to skip that step.
            login(request, user)

            # Redirect to dashboard after successful signup + login.
            # Using redirect() (not render()) is deliberate — see note below.
            return redirect('dashboard')
        # If form.is_valid() is False, we fall through to the render() at the bottom,
        # which re-shows the form — now populated with Django's validation error messages.
    else:
        # GET request — user is just visiting /signup/ for the first time.
        # Create a blank, unbound form instance to display.
        form = SignUpForm()

    # This line runs for: GET requests, AND failed POST requests (falls through from above)
    return render(request, 'registration/signup.html', {'form': form})









"""
home view 
- Rendered when 
    - the user first lands on the wesbite without logging in OR 
    - when they log out 
"""

def home(request) : 
    # request.user is Django's way of telling us who's making this request.
    # is_authenticated is a boolean: True if someone is logged in, False if anonymous.
    if request.user.is_authenticated : 
        # Bounce logged-in users straight to their dashboard
        # 'dashboard' here is a URL NAME (defined in urls.py)
        return redirect('dashboard')

    # If we reach this line, the user is NOT logged in — show the public home page.
    return render(request, 'stocks/home.html')












"""
dashboard view
- Opens when the user Logs In. It aggregates a specific user's data  
- Contains : 
    - UserPinned Stocks 
    - User Portfolio 
    - Price Alerts
"""

# This decorator ensures that django checks if the user is authenticated BEFORE every running the dashboard function's code
    # If they are logged in → dashboard runs normally
    # If they're not → Django auto-redirects them to your login page, and dashboard's code never executes at all 
@login_required
def dashboard(request) : 
    # request.user.username is available because Django's auth system resolved who this user is
    # before the function even runs
    return HttpResponse(f"Welcome to your dashboard : {request.user.username}!")












##############################################################################################################










"""
stock_detail view
- Creates the Stock row in the model and Displays a specific stock's data. Contains the default chart (1M) and the prices 
- Executed when : 
    - User selects a stock from the search 
    - User selects a stock from their dashboard 

"""



def stock_detail(request, ticker) : 
    # this is the FIRST time a Stock row might come into existence for this ticker.
    stock, created = Stock.objects.get_or_create(
        ticker=ticker,
        defaults={'name': ticker}  # temporary placeholder name, replaced below if newly created
    )
    
    
    if created : 
        # Only spend the extra yfinance call getting the proper long name if this Stock row didn't already exist. 
        # Existing stocks already have a real name — no need to re-fetch it every visit.
        long_name = fetch_stock_name(ticker)
        if long_name:
            stock.name = long_name
            stock.save()



    # Pull current price + a default range of history, using the service layer we already built and tested 
    price, price_is_stale = get_current_price(stock)
    history, history_is_stale = get_price_history(stock, "1M")
    
    
    # Placeholder
    return HttpResponse(
        f"{stock.name} ({stock.ticker})<br>"
        f"Price: {price} (stale: {price_is_stale})<br>"
        f"History points: {len(history) if history else 0} (stale: {history_is_stale})"
    )
    









"""
stock_history view 
- This will be our chart data endpoint 
- It will give the JS the JSON data required to redraw the chart without reloading the entire stock_detail view

"""


def stock_history(request, ticker, range_code) : 
    
    # Validate range_code against the same choices already defined on the model 
    valid_ranges = [choice[0] for choice in StockHistoryCache.RANGE_CHOICES]
    
    if range_code not in valid_ranges:
        # status=400 = "Bad Request" — tells the JS that the request itself was malformed, not that the server broke.
        return JsonResponse({'error': 'Invalid range'}, status=400)
    
    # get_object_or_404: like Stock.objects.get(), but returns a proper 404
    # automatically instead of raising an unhandled exception if no matching Stock exists. 
    # We use a plain lookup (not get_or_create) here because this endpoint should only ever get hit AFTER stock_detail already
    # created the Stock row — this isn't a creation point.
    stock = get_object_or_404(Stock, ticker = ticker)
    
    # Get the price history of the stock for the new range
    data, is_stale = get_price_history(stock, range_code)

    # JsonResponse serializes this dict into actual JSON text and sets the
    # correct Content-Type header for us — this is what JavaScript will
    # eventually call via fetch() to redraw the chart.
    return JsonResponse({
        'ticker': stock.ticker,
        'range': range_code,
        'data': data,
        'is_stale': is_stale,
    })




















#################################################################################################################









"""
watchlist views 
- 3 distinct views serving separate functions 
    1) watchlist_add : Adds a stock to the user's watchlist
    2) watchlist_remove : Removes the stock from the user's watchlist
    3) watchlist_view : Returns all the stocks in the user's watchlist 
    
"""

@login_required
def watchlist_view(request) : 
    # Filters WatchlistItem down to ONLY the logged-in user's rows
    items = WatchlistItem.objects.filter(user = request.user)
    
    # Build a simple placeholder response listing tickers
    tickers = ", ".join(item.stock.ticker for item in items)
    return HttpResponse(f"Your watchlist: {tickers if tickers else '(empty)'}")






@login_required 
def watchlist_add(request, ticker) :
    
    # The get_or_create() handles both cases : 
        # 1) User added a stock to watchlist directly from the search without visiting the stock_detail page : 
        #    - In this case, the stock might not exist in the model and will need to be created 
        # 2) User visited the stock_detail page AND then added a stock to watchlist
        #    - In this case, the stock will exist in the model since the stock_detail page handles the creation of the row 
    stock, created = Stock.objects.get_or_create(
        ticker = ticker, 
        defaults = {'name', ticker}     # temporary placeholder name, replaced below if newly created     
    )                                              
    
    
    
    # IF a new row was created : GET the long_name of the stock 
    if created : 
        long_name = fetch_stock_name(ticker)
        if long_name : 
            stock.name = long_name 
            stock.save()
    
    
    # Adding the stock to the watchlist 
    # The get_or_create() handles a different function here : 
        # Prevents duplicate watchlist rows if user clicks "add" multiple times
    WatchlistItem.objects.get_or_create(
        user = request.user, 
        stock = stock
    )
            

    # After adding, send the user back to the stock's detail page —
    # 'stock_detail' is the URL name, and it needs the ticker
    # passed as a keyword argument since that URL requires one.
    return redirect('stock_detail', ticker=ticker)









@login_required
def watchlist_remove(request, ticker) : 
    stock = get_object_or_404(Stock, ticker = ticker)
    
    # filter().delete() instead of get().delete()
    # If for some reason the WatchlistItem does not exist, filter() just deletes zero rows silently rather than raising an error
    WatchlistItem.objects.filter(user=request.user, stock=stock).delete()
    
    return redirect('stock_detail', ticker=ticker)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    