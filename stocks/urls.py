from django.urls import path 
from . import views    # your app's views.py, where signup_view lives



"""
The path() function defines the following:
    1) A URL Pattern 
    2) A view function that will be called if the URL pattern is detected
    3) A name so that you can refer to the URL in your HTML templates

"""



urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('', views.home, name = 'home'), 
    path('dashboard/', views.dashboard, name = 'dashboard')
]