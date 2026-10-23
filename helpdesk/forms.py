from django import forms

class ExcelInputForm(forms.Form):
    excel_file = forms.FileField(
        label='Выберите Excel-файл для загрузки'
    )