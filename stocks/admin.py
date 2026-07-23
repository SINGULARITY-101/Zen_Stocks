from django.contrib import admin
from .models import Stock, WatchlistItem, PortfolioHolding, PriceAlert, StockHistoryCache, StockPriceCache

# Register your models here.

# admin.site.register() tells Django: "expose this model in the admin UI"
admin.site.register(Stock)
admin.site.register(WatchlistItem)
admin.site.register(PortfolioHolding)
admin.site.register(PriceAlert)
admin.site.register(StockPriceCache)
admin.site.register(StockHistoryCache)