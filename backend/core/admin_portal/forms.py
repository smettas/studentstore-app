from django import forms
from catalog.models import Product

class StockForm(forms.Form):
    product_id = forms.ModelChoiceField(queryset=Product.objects.all(), to_field_name="id")
    new_stock = forms.IntegerField(min_value=0, max_value=100000000)
