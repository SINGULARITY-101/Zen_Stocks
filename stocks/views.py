from django.shortcuts import render, redirect
from django.contrib.auth import login  # logs a user in by attaching them to the session
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm  # the form we just built

from django.http import HttpResponse



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
- Opens when the user 
    - Logs In  
"""

# This decorator ensures that django checks if the user is authenticated BEFORE every running the dashboard function's code
    # If they are logged in → dashboard runs normally
    # If they're not → Django auto-redirects them to your login page, and dashboard's code never executes at all 
@login_required
def dashboard(request) : 
    # request.user.username is available because Django's auth system resolved who this user is
    # before the function even runs
    return HttpResponse(f"Welcome to your dashboard : {request.user.username}!")
