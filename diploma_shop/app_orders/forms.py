from django import forms


class BasketDeleteForm(forms.Form):
    id = forms.IntegerField()
    count = forms.IntegerField()
