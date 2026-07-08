from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm) : 

    # We're adding an email field that doesn't exist on the base UserCreationForm.
    # required=True means the form won't validate without it — Django's User model
    # technically allows a blank email, but we're choosing to enforce it here.
    email = forms.EmailField(required=True)
    
    
    class Meta :
        # Meta tells Django "this form is based on the User model" — 
        # it's what makes save() know which table to write to. 
        model = User 
        
        # We explicitly list which fields appear on the form, in order.
        # UserCreationForm already defines username/password1/password2 internally —
        # we're just inserting 'email' into that list.
        fields = ['username', 'email', 'password1', 'password2']
    