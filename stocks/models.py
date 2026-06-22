from django.db import models
from django.conf import settings    # Use this instead of importing user directly






# --- SHARED REFERENCE TABLE ---
# This stores what a stock IS, not what a user does with it.
# One row per ticker. Multiple users can reference the same row.

class Stock(models.Model) : 
    ticker = models.CharField(max_length=10, unique=True)   # e.g. "AAPL" — unique enforced at DB level
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
        related_name = 'watchlist'           # lets you do user.watchlist.all() later
    )
    
    
    # Field 2
    stock = models.ForeignKey(
        Stock, 
        on_delete = models.CASCADE,           # If a stock is removed, drop it from all watchlists
        related_name = 'watched_by'
    )
    
    
    # Field 3
    added_at = models.DateTimeField(auto_now_add = True)    # Auto-set when row is created
    
    
    
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