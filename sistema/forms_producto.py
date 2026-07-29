from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto

        fields = [
            'nombre',
            'descripcion',
            'precio',
            'categoria',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control'
            }),

            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),

            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")

        if precio is not None and precio < 0:
            raise forms.ValidationError(
                "No se permiten números negativos."
            )

        return precio