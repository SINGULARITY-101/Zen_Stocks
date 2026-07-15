from django.db import models
from django.conf import settings    # Use this instead of importing user directly



"""
MODEL DIAGRAM
                    +-----------+
                    |   USER    |
                    +-----------+
                    | id (PK)   |
                    | username  |
                    +-----------+
                     /    |    \
                    /     |     \
                   /      |      \
                  /       |       \
                 /        |        \
                /         |         \
               v          v          v

      +---------------+  +-------------------+  +---------------+
      | WATCHLISTITEM |  | PORTFOLIOHOLDING  |  |  PRICEALERT   |
      +---------------+  +-------------------+  +---------------+
      | id (PK)       |  | id (PK)           |  | id (PK)       |
      | user_id (FK)  |  | user_id (FK)      |  | user_id (FK)  |
      | stock_id (FK) |  | stock_id (FK)     |  | stock_id (FK) |
      | added_at      |  | shares            |  | target_price  |
      +---------------+  | avg_cost          |  | direction     |
                         +-------------------+  | is_active     |
                                                +---------------+
                ^          ^          ^ 
                 \         |         /
                  \        |        /
                   \       |       /
                    \      |      /
                     \     |     /
                      \    |    /

                    +-----------+
                    |   STOCK   |
                    +-----------+
                    | id (PK)   |
                    | ticker    |
                    | name      |
                    +-----------+
                     ^         ^
                    /           \
                   /             \
                  /               \
                 /                 \

  +---------------------+   +------------------------+
  |  STOCKPRICECACHE     |   |  STOCKHISTORYCACHE     |
  +---------------------+   +------------------------+
  | id (PK)              |   | id (PK)                 |
  | stock_id (FK, 1-to-1)|   | stock_id (FK)           |
  | price                |   | range (1W/1M/6M/1Y)     |
  | last_updated         |   | data (JSON)             |
  +---------------------+    | last_updated            |
                             +------------------------+
                             unique_together:
                             (stock_id, range)

"""





# --- SHARED REFERENCE TABLE ---
# This stores what a stock IS, not what a user does with it.
# One row per ticker. Multiple users can reference the same row.

class Stock(models.Model) : 
    ticker = models.CharField(max_length=20, unique=True)   # e.g. "AAPL" — unique enforced at DB level
    name = models.CharField(max_length=255)                 # e.g. "Apple Inc."

    
    def __str__(self):
        return f"{self.ticker} - {self.name}"               # Clean display in admin and shell







# --- USER'S WATCHLIST ---
# "User X is watching Stock Y since date Z"
# unique_together prevents the same stock being pinned twice by the same user

class WatchlistItem(models.Model) : 
    # Field 1 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,            # Points to Django's User model (auth-safe pattern)
        on_delete = models.CASCADE,          # If user is deleted, remove their watchlist too
        related_name = 'watchlist'           # lets you walk the relationship backwards : user.watchlist.all() later
    )
    
    
    # Field 2
    stock = models.ForeignKey(
        Stock, 
        on_delete = models.CASCADE,           # If a stock is removed, drop it from all watchlists
        related_name = 'watched_by'
    )
    
    
    # Field 3
    added_at = models.DateTimeField(auto_now_add = True)    # Auto-set when row is created and never touch it again
                                                            # Its brother : `auto_now = True` updates on every save
    
    
    
    
    # Useful for declaring model-level properties (ordering, constraints, etc.)
    class Meta:
        unique_together = ('user', 'stock')    # One pin per stock per user
    
    
    def __str__(self) : 
        return f"{self.user.username} watching {self.stock.ticker}"
    
    
    
    
    




# --- USER'S PORTFOLIO ---
# "User X owns N shares of Stock Y, bought at price Z"

class PortfolioHolding(models.Model) : 
    # Field 1 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='holdings'
    )
    
    
    # Field 2 
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='held_by'
    )


    # Field 3 
    shares = models.DecimalField(max_digits=10, decimal_places=4)       # e.g. 10.5000 shares
    # Field 4 
    avg_cost = models.DecimalField(max_digits=10, decimal_places=2)     # average buy price in $
    # Field 5
    added_at = models.DateTimeField(auto_now_add=True)
    
    
    
    class Meta:
        unique_together = ('user', 'stock')  # One holding per stock per user (simplification for MVP)


    def __str__(self):
        return f"{self.user.username}: {self.shares} shares of {self.stock.ticker}"











# --- PRICE ALERTS ---
# "Alert me when Stock Y goes ABOVE/BELOW price Z"
class PriceAlert(models.Model):
    ABOVE = 'above'
    BELOW = 'below'
    DIRECTION_CHOICES = [
        (ABOVE, 'Above'),
        (BELOW, 'Below'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    
    
    target_price = models.DecimalField(max_digits=10, decimal_places=2)   # the trigger price
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)  # above or below
    is_active = models.BooleanField(default=True)   # flip to False once triggered
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: alert if {self.stock.ticker} goes {self.direction} ${self.target_price}"





















# --- STOCK PRICES ---

# Holds the current price of a stock 
class StockPriceCache(models.Model) : 
    # OneToOne, not ForeignKey — each Stock gets exactly ONE current-price row, never multiple. ForeignKey would 
    # technically allow duplicates for the same stock, which makes no sense for "the current price."
    stock = models.OneToOneField(Stock, on_delete = models.CASCADE)
    

    # DecimalField, not FloatField — prices should never use floating point,
    # since floats introduce rounding errors (e.g. 19.999999999 instead of 20.00).
    # max_digits=10, decimal_places=2 → supports up to 99,999,999.99
    price = models.DecimalField(max_digits=10, decimal_places = 2)
    
    # `auto_now = True` updates the row on every save
    last_updated = models.DateTimeField(auto_now = True)
    
    def __str__(self):
        return f"{self.stock.ticker} @ {self.price} ({self.last_updated})"
    
    
    
    
    
# Holds the historical price data of a stock 
class StockHistoryCache(models.Model) : 
    # ForeignKey (not OneToOne) — deliberately allows MULTIPLE rows per stock, because each (stock, range) pair is its own row. 
    # AAPL/"1W" and AAPL/"1Y" are two separate rows here.
    stock = models.ForeignKey(Stock, on_delete = models.CASCADE)
    
    
    # A fixed set of allowed values — 'choices' restricts what can be saved here,
    # catching typos like "1w" vs "1W" at the database/form level rather than silently accepting garbage.
    RANGE_CHOICES = [
        ('1W', '1 Week'), 
        ('1M', '1 Month'), 
        ('6M', '6 Months'), 
        ('1Y', '1 Year'), 
    ]    
    range = models.CharField(max_length = 2, choices = RANGE_CHOICES)
    
    # JSONField stores the actual time-series data as JSON
    data = models.JSONField()
    
    last_updated = models.DateTimeField(auto_now = True)
    
    
    
    class Meta : 
        # Enforces at the database level: only ONE row can exist for a given (stock, range) combination. 
        # Prevents duplicate/conflicting cache rows for the same stock+range pair.
        unique_together = ('stock', 'range')
        
    
    def __str__(self) : 
        return f"{self.stock.ticker} - {self.range} ({self.last_updated})"