from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class RegistroForm(UserCreationForm):

    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_password1(self):

        password = self.cleaned_data.get('password1')

        if len(password) < 8:
            raise ValidationError(
                "La contraseña debe tener mínimo 8 caracteres."
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Debe contener al menos una letra mayúscula."
            )

        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "Debe contener al menos un número."
            )

        if not re.search(r'[\W_]', password):
            raise ValidationError(
                "Debe contener al menos un carácter especial."
            )

        return password