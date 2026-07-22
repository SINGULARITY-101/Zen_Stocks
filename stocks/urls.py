from django.urls import path 
from . import views    # your app's views.py, where signup_view lives



"""
The path() function defines the following:
    1) A URL Pattern 
    2) A view function that will be called if the URL pattern is detected
    3) A name so that you can refer to the URL in your HTML templates

<str:ticker> is a path converter 
    - It tells Django "capture whatever's in this URL segment as a string, and pass it into the view function as an argument named ticker." 
    - So visiting /stock/INFY.NS/ calls stock_detail(request, ticker="INFY.NS") automatically. 
    - The . in INFY.NS isn't a problem — str converters accept any character except /.

"""



urlpatterns = [
    path('', views.home, name = 'home'), 
    path('signup/', views.signup_view, name='signup'),
        
    path('dashboard/', views.dashboard, name = 'dashboard'), 
    
    path('stock/<str:ticker>/', views.stock_detail, name='stock_detail'), 
    path('stock/<str:ticker>/history/<str:range_code>/', views.stock_history, name='stock_history'), 
    
    path('watchlist/', views.watchlist_view, name='watchlist_view'),
    path('watchlist/add/<str:ticker>/', views.watchlist_add, name='watchlist_add'),
    path('watchlist/remove/<str:ticker>/', views.watchlist_remove, name='watchlist_remove')
]