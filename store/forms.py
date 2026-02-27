# store/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Order

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'popup-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'popup-input'}))

class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=10, initial=1)
    size = forms.ChoiceField(choices=[
        ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL')
    ])
    
    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product:
            available_sizes = product.available_sizes()
            self.fields['size'].choices = [(size, size) for size in available_sizes]

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'city', 'postal_code']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'popup-input'}),
            'last_name': forms.TextInput(attrs={'class': 'popup-input'}),
            'email': forms.EmailInput(attrs={'class': 'popup-input'}),
            'address': forms.TextInput(attrs={'class': 'popup-input'}),
            'city': forms.TextInput(attrs={'class': 'popup-input'}),
            'postal_code': forms.TextInput(attrs={'class': 'popup-input'}),
        }