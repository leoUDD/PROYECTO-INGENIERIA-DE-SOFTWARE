
from django import forms

class UploadExcelForm(forms.Form):
    file = forms.FileField(label="Selecciona un archivo Excel (.xlsx o .xls)")
