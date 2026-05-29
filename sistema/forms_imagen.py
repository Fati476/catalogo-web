from django import forms
from .models import ProductoImagen


class ProductoImagenForm(forms.ModelForm):

    class Meta:

        model = ProductoImagen

        fields = ['imagen']