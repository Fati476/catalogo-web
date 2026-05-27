from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
import re


class RegistroForm(UserCreationForm):

    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


    def clean_username(self):

        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():

            raise forms.ValidationError(
                "Ese nombre de usuario ya existe."
            )

        return username


    def clean_password1(self):

        password = self.cleaned_data.get('password1')

        if len(password) < 8:
            raise forms.ValidationError(
                "La contraseña debe tener mínimo 8 caracteres."
            )

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )

        if not re.search(r"[0-9]", password):
            raise forms.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        if not re.search(r"[\W_]", password):
            raise forms.ValidationError(
                "La contraseña debe contener un carácter especial."
            )

        return password