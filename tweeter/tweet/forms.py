from django import forms 
from .models import Tweet
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class Tweetform(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'What’s happening?',
            'rows': 4,
        })
    )
    photo = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file'
        })
    )
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Title'
        })
    )

    collaborators = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter collaborator emails separated by commas'
        })
    )
    class Meta:
        model = Tweet
        fields = ('text', 'photo', 'title', 'collaborators')

    def clean_collaborators(self):
        collaborators = self.cleaned_data.get('collaborators')
        if collaborators:
            data = self.cleaned_data['collaborators']
        if not data:
            return []

        emails = [email.strip() for email in data.split(',') if email.strip()]
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(f"Invalid email: {email}")
        return emails



class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        }),
        label='Email Address'
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        }),
        label='Username'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        label='Password'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')