
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django import forms
import re
import json
from pathlib import Path


class RegistroForm(UserCreationForm):

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    telefono = forms.CharField(max_length=10)
    estado = forms.CharField(max_length=100)
    municipio = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]

    def clean_first_name(self):
        nombre = self.cleaned_data.get('first_name', '').strip()

        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")

        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÜüÑñ ]+", nombre):
            raise forms.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )

        return nombre

    def clean_last_name(self):
        apellidos = self.cleaned_data.get('last_name', '').strip()

        if not apellidos:
            raise forms.ValidationError("Los apellidos son obligatorios.")

        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÜüÑñ ]+", apellidos):
            raise forms.ValidationError(
                "Los apellidos solo pueden contener letras y espacios."
            )

        return apellidos

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ese correo ya está registrado."
            )

        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()

        if not re.fullmatch(r"[0-9]{10}", telefono):
            raise forms.ValidationError(
                "El teléfono debe contener exactamente 10 dígitos."
            )

        return telefono

    def clean_estado(self):
        estado = self.cleaned_data.get('estado', '').strip()
        municipios_data = self.obtener_municipios()

        if estado not in municipios_data:
            raise forms.ValidationError(
                "Selecciona un estado válido."
            )

        return estado

    def clean_municipio(self):
        municipio = self.cleaned_data.get('municipio', '').strip()
        estado = self.data.get('estado', '').strip()
        municipios_data = self.obtener_municipios()

        if estado not in municipios_data:
            raise forms.ValidationError(
                "Selecciona primero un estado válido."
            )

        if municipio not in municipios_data[estado]:
            raise forms.ValidationError(
                "Selecciona un municipio válido para el estado elegido."
            )

        return municipio

    @staticmethod
    def obtener_municipios():
        ruta_json = (
            Path(__file__).resolve().parent
            / 'static'
            / 'json'
            / 'municipios.json'
        )

        try:
            with ruta_json.open(encoding='utf-8') as archivo:
                return json.load(archivo)
        except (OSError, json.JSONDecodeError):
            raise forms.ValidationError(
                "No fue posible validar los estados y municipios. Intenta más tarde."
            )

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

        if not re.fullmatch(r"[A-Za-z0-9@#$!%&*?_.-]+", password):
            raise forms.ValidationError(
                "La contraseña solo puede contener letras, números y estos símbolos: @ # $ ! % & * ? _ - ."
            )

        if not re.search(r"[@#$!%&*?_.-]", password):
            raise forms.ValidationError(
                "La contraseña debe contener al menos un carácter especial permitido."
            )

        return password


class CustomSetPasswordForm(SetPasswordForm):

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")

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

        if not re.fullmatch(r"[A-Za-z0-9@#$!%&*?_.-]+", password):
            raise forms.ValidationError(
                "La contraseña solo puede contener letras, números y estos símbolos: @ # $ ! % & * ? _ - ."
            )

        if not re.search(r"[@#$!%&*?_.-]", password):
            raise forms.ValidationError(
                "La contraseña debe contener al menos un carácter especial permitido."
            )

        return password
