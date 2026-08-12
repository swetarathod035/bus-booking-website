from django import forms
from .models import Bus, Driver


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = [
            'bus_number', 'bus_name', 'bus_type', 'total_seats',
            'status', 'manufacturer', 'model_year', 'registration_expiry',
            'insurance_expiry', 'image', 'has_wifi', 'has_ac', 'has_charging', 'has_gps'
        ]
        widgets = {
            'bus_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bus_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bus_type': forms.Select(attrs={'class': 'form-select'}),
            'total_seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 60}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'insurance_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            'name', 'employee_id', 'license_number', 'phone', 'email',
            'photo', 'status', 'assigned_bus', 'experience_years',
            'joining_date', 'license_expiry'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_bus': forms.Select(attrs={'class': 'form-select'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'license_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
