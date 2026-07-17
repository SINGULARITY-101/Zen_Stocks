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
    path('signup/', views.signup_view, name='signup'),
    path('', views.home, name = 'home'), 
    path('dashboard/', views.dashboard, name = 'dashboard'), 
    path('stock/<str:ticker>/', views.stock_detail, name='stock_detail')
]