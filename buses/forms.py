from django import forms
from .models import Bus, Driver
from routes.models import Route, Schedule, Stop
from accounts.models import CustomUser
from bookings.models import PassScheme, BusPass


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = [
            'bus_number', 'bus_name', 'bus_type', 'total_seats',
            'status', 'manufacturer', 'model_year', 'registration_expiry',
            'insurance_expiry', 'image', 'has_wifi', 'has_ac', 'has_charging', 'has_gps'
        ]
        widgets = {
            'bus_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. GJ-07-AB-1234'}),
            'bus_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Anand Superfast'}),
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


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = [
            'route_number', 'route_name', 'source', 'destination',
            'distance_km', 'base_fare', 'fare_per_km', 'status', 'description'
        ]
        widgets = {
            'route_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. R-101'}),
            'route_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Anand Stand to Vidyanagar'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'destination': forms.Select(attrs={'class': 'form-select'}),
            'distance_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'base_fare': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'fare_per_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = [
            'route', 'bus', 'driver', 'travel_date', 'departure_time',
            'arrival_time', 'day_type', 'status', 'available_seats', 'notes'
        ]
        widgets = {
            'route': forms.Select(attrs={'class': 'form-select'}),
            'bus': forms.Select(attrs={'class': 'form-select'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'travel_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'departure_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'arrival_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'day_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'available_seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class StopForm(forms.ModelForm):
    class Meta:
        model = Stop
        fields = ['code', 'name', 'latitude', 'longitude', 'address', 'is_major', 'image']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. VV_NAGAR'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vallabh Vidyanagar'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_major': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'is_active', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PassSchemeForm(forms.ModelForm):
    class Meta:
        model = PassScheme
        fields = [
            'name', 'scheme_type', 'description', 'validity_days',
            'price', 'discount_pct', 'unlimited_trips', 'trip_limit',
            'applicable_routes', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'scheme_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'validity_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'discount_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'trip_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'applicable_routes': forms.CheckboxSelectMultiple(),
        }
