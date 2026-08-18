from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login  # logs a user in by attaching them to the session
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse


from .forms import SignUpForm  # the form we just built
from .models import Stock, StockHistoryCache, WatchlistItem, PortfolioHolding, PriceAlert
from .services import get_current_price, get_price_history, fetch_stock_name # all api calls exist here

from decimal import Decimal, InvalidOperation






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
    # Check if we already have this stock — no validation needed if so,
    # since a row only ever gets created below AFTER being confirmed real.
    stock = Stock.objects.filter(ticker=ticker).first()

    if not stock:
        # Ticker not seen before — validate it's real BEFORE writing anything.
        long_name = fetch_stock_name(ticker)
        if not long_name:
            # yfinance couldn't find this ticker at all — don't create a Stock row for garbage input.
            return HttpResponse("Stock not found.", status=404)

        # Ticker found, create the row in the stock model
        stock = Stock.objects.create(ticker=ticker, name=long_name)



    # Pull current price + a default range of history, using the service layer we already built and tested 
    price, previous_close, price_is_stale = get_current_price(stock)
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
    
    # Same pattern as the fixed stock_detail: look first, don't create blindly.
    stock = Stock.objects.filter(ticker=ticker).first()

    if not stock:
        # Ticker not seen before — validate it's real BEFORE writing anything.
        long_name = fetch_stock_name(ticker)
        if not long_name:
            # Invalid ticker — don't create a Stock row, don't add to watchlist, fail cleanly instead.
            return HttpResponse("Stock not found.", status=404)

        # Ticker found, create the row in the stock model
        stock = Stock.objects.create(ticker=ticker, name=long_name)
    
    
    # Adding the stock to the watchlist 
    # The get_or_create() handles a different function here : 
        # Prevents duplicate watchlist rows if user clicks "add" multiple times
    WatchlistItem.objects.get_or_create(
        user = request.user, 
        stock = stock
    )
            

    # Check if the caller specified where to return to. If not, fall back to stock_detail as a sane default.
    next_url = request.GET.get('next')
    
    if next_url:
        return redirect(next_url)
    return redirect('stock_detail', ticker=ticker)














@login_required
def watchlist_remove(request, ticker) : 
    stock = get_object_or_404(Stock, ticker = ticker)
    
    # filter().delete() instead of get().delete()
    # If for some reason the WatchlistItem does not exist, filter() just deletes zero rows silently rather than raising an error
    WatchlistItem.objects.filter(user=request.user, stock=stock).delete()
    
    
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('stock_detail', ticker=ticker)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#######################################################################################################








"""
portfolio views 
- User will be able to : 
    - Add stocks to their portfolio 
        - Weighted average calculated when the same stock is bought multiple times
        
    - Sell the stocks from their portfolio 
        - Partial selling is allowed
        - The stock in the portfolio stays until it reaches 0
    
    - View their whole portfolio and check their net gain/loss



TODO : Currently accepting shares and avg_cost as URL query parameters till we create the template in Phase 4
     : /portfolio/add/RELIANCE.NS/?shares=10&price=1300
"""






@login_required

def portfolio_add(request, ticker) : 
    # The query parameters come back as strings. We will need to convert them ourselves.
    shares_param = request.GET.get('shares')
    price_param = request.GET.get('price') 
    
    try : 
        # Will be using Decimal to avoid rounding errors that float introduces 
        new_shares = Decimal(shares_param)
        new_cost = Decimal(price_param)
             
    except (InvalidOperation, TypeError) : 
        # InvalidOperation: the string wasn't a valid number (e.g. "abc").
        # TypeError: the param was missing entirely (None passed to Decimal).
        return HttpResponse("Invalid or missing shares/avg_cost.", status=400)

    if new_shares <= 0 or new_cost <= 0:
        return HttpResponse("Shares and cost must be positive.", status=400)
    
    
    
    # Check if the ticker already exists in the Stock model 
    stock = Stock.objects.filter(ticker = ticker).first()
    
    # Stock does not exist : Check if the ticker is valid
    if not stock : 
        long_name = fetch_stock_name(ticker)
        
        # Could not find the long_name from yfinance : Ticker is invalid
        if not long_name : 
            return HttpResponse("Stock not found.", status=404)
        
        # Ticker found : Create the row 
        stock = Stock.objects.create(ticker = ticker, name = long_name)
    
    
    
    # Check if the stock is already in the user's portfolio 
    holding = PortfolioHolding.objects.filter(user = request.user, stock = stock).first()
    
    
    # IF the user already owns the stock : Calculate the weighted average to update the exisitng stock row
    if holding : 
        # Weighted average cost — the actual "merge" logic.
        # Total money already invested + total money just invested / total shares now held.
        total_existing_cost = holding.shares * holding.avg_cost
        total_new_cost = new_shares * new_cost
        combined_shares = holding.shares + new_shares

        holding.avg_cost = (total_existing_cost + total_new_cost) / combined_shares
        holding.shares = combined_shares
        holding.save()
    
    # ELSE the user does not already own the stock : Create a new row in their portfolio
    else : 
        PortfolioHolding.objects.create(
            user = request.user, 
            stock = stock, 
            shares = new_shares, 
            avg_cost = new_cost
        )
    
    
    
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('stock_detail', ticker=ticker)
        
    
    







    
@login_required

def portfolio_remove(request, ticker) : 
    sell_param = request.GET.get('shares')
    
    try:
        sell_shares = Decimal(sell_param)
    
    except (InvalidOperation, TypeError):
        return HttpResponse("Invalid or missing shares.", status=400)

    if sell_shares <= 0:
        return HttpResponse("Shares must be positive.", status=400)
    
    
    
    # Fetch the stock details from the Stock model
    # Fetch the portfolio details for that stock from the user's portfolio 
    stock = get_object_or_404(Stock, ticker=ticker)
    holding = get_object_or_404(PortfolioHolding, user=request.user, stock=stock)


    if sell_shares >= holding.shares:
        # Selling all (or somehow more than) what's held — remove the
        # holding entirely rather than leaving a zero/negative row.
        holding.delete()
    
    else:
        # Partial sell: reduce shares, avg_cost stays UNCHANGED.
        # Selling some shares doesn't change what you paid for the ones you still hold 
        holding.shares -= sell_shares
        holding.save()
    
    

    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('stock_detail', ticker=ticker)
    
    
    
    
    
    
    
    
    
    
    
    
    
@login_required

def portfolio_view(request) : 
    holdings = PortfolioHolding.objects.filter(user=request.user)
    lines = []
    
    for holding in holdings : 
        # Get the price of each stock in their portfolio
        current_price, previous_close, is_stale = get_current_price(holding.stock)
        
        # Found the current price : calculate the net gain/loss
        if current_price : 
            current_value = holding.shares * current_price
            invested = holding.shares * holding.avg_cost
            gain_loss = current_value - invested 
            
            lines.append(
                f"{holding.stock.ticker}: {holding.shares} shares @ avg ₹{holding.avg_cost} "
                f"→ now ₹{current_price} | Gain/Loss: ₹{gain_loss} (stale: {is_stale})"
            )
        
        # Could not find the price
        else : 
            lines.append(f"{holding.stock.ticker}: price unavailable")
            

    return HttpResponse("<br>".join(lines) if lines else "Your portfolio is empty.")




















##########################################################################################################################














"""
Price Alert Views
- alert_add : User will add the stock they want price alerts for 
- alert_remove : User will remove the stock they don't want price alerts for
- alert_view : All price alerts the user has added


- An email will be sent whenever the price goes ABOVE or BELOW the target price




TODO : The checking of price alerts and the notifcations will be done in PHASE 6
     : Initially accepting target price and direction as URL query parameters. Will update it later to take form input.
"""





@login_required

def alert_add(request, ticker) : 
    # Get the URL query parameters
    target_param = request.GET.get('target_price')
    direction_param = request.GET.get('direction')

    # Input Validation
    try:
        target_price = Decimal(target_param)
    except (InvalidOperation, TypeError):
        return HttpResponse("Invalid or missing target_price.", status=400)

    if target_price <= 0:
        return HttpResponse("target_price must be positive.", status=400)

    # Check whether the direction passed is valid or not
    if direction_param not in (PriceAlert.ABOVE, PriceAlert.BELOW):
        return HttpResponse("direction must be 'above' or 'below'.", status=400)




    # Creating a valid stock row in the Stock Model if needed just like how we did it in other views
    stock = Stock.objects.filter(ticker = ticker).first()
    if not stock:
        long_name = fetch_stock_name(ticker)
        if not long_name:
            return HttpResponse("Stock not found.", status=404)
        stock = Stock.objects.create(ticker=ticker, name=long_name)

        
        
    
    # update_or_create: lookup fields identify WHICH alert (user, stock, direction) — defaults are what gets SET, 
    # whether creating new or updating an existing one
    PriceAlert.objects.update_or_create(
        user=request.user,
        stock=stock,
        direction=direction_param,
        defaults={'target_price': target_price, 'is_active': True}
    )
    


    # Redirecting to the appropriate URL
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('stock_detail', ticker=ticker)
    
    
    
    











@login_required
def alert_remove(request, alert_id) : 
    # Alerts are identified by their OWN id. This ID is auto-generated in the model by django 
    alert = get_object_or_404(PriceAlert, id = alert_id, user=request.user)
    ticker = alert.stock.ticker  # grab this before deleting, we need it below
    alert.delete()
    
    
    # Redirecting to the appropriate URL
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('stock_detail', ticker=ticker)
    













@login_required
def alert_view(request) : 
    # Will only show alerts that UNTRIGGERED
    # For UNTRIGGERED alerts : is_active = True will indicate that the alert is still being watched
    # For TRIGGERED alerts : is_active = False will indicate that the alert is not being watched by the background job
    alerts = PriceAlert.objects.filter(user = request.user, is_active = True)

    lines = [
        f"{a.id}: {a.stock.ticker} — alert if {a.direction} ₹{a.target_price}"
        for a in alerts
    ]
    return HttpResponse("<br>".join(lines) if lines else "No active alerts.")