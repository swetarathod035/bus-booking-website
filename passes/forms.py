from django import forms
from .models import BusPass, SpecialScheme, SchemeApplication
from routes.models import Route, Stop


class StudentPassForm(forms.ModelForm):
    class Meta:
        model = BusPass
        fields = [
            'applicant_name', 'email', 'phone', 'route',
            'start_stop', 'end_stop', 'duration_months',
            'college_name', 'student_id_number', 'id_proof_number', 'id_proof_document'
        ]
        widgets = {
            'applicant_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name (as per Student ID)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@college.edu.in'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'route': forms.Select(attrs={'class': 'form-select', 'id': 'id_route'}),
            'start_stop': forms.Select(attrs={'class': 'form-select', 'id': 'id_start_stop'}),
            'end_stop': forms.Select(attrs={'class': 'form-select', 'id': 'id_end_stop'}),
            'duration_months': forms.Select(
                choices=[
                    (1, '1 Month (50% Student Subsidy)'),
                    (3, '3 Months (60% Student Subsidy)'),
                    (6, '6 Months (65% Student Subsidy)'),
                    (12, '12 Months / 1 Year (70% Student Subsidy)'),
                ],
                attrs={'class': 'form-select', 'id': 'id_duration_months'}
            ),
            'college_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BVM Engineering College, V.V. Nagar'}),
            'student_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College Roll No / Enrollment ID'}),
            'id_proof_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aadhaar Card No / Government ID'}),
            'id_proof_document': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PassengerPassForm(forms.ModelForm):
    class Meta:
        model = BusPass
        fields = [
            'applicant_name', 'email', 'phone', 'route',
            'start_stop', 'end_stop', 'duration_months',
            'id_proof_number', 'id_proof_document'
        ]
        widgets = {
            'applicant_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'route': forms.Select(attrs={'class': 'form-select', 'id': 'id_route'}),
            'start_stop': forms.Select(attrs={'class': 'form-select', 'id': 'id_start_stop'}),
            'end_stop': forms.Select(attrs={'class': 'form-select', 'id': 'id_end_stop'}),
            'duration_months': forms.Select(
                choices=[
                    (1, '1 Month Express Commuter (20% Off)'),
                    (3, '3 Months Quarterly Pass (30% Off)'),
                    (6, '6 Months Half-Yearly Pass (35% Off)'),
                    (12, '12 Months VIP Commuter Pass (40% Off)'),
                ],
                attrs={'class': 'form-select', 'id': 'id_duration_months'}
            ),
            'id_proof_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aadhaar Card No / Driving License / Voter ID'}),
            'id_proof_document': forms.FileInput(attrs={'class': 'form-control'}),
        }


class SpecialSchemeForm(forms.ModelForm):
    class Meta:
        model = SpecialScheme
        fields = [
            'title', 'code', 'target_audience', 'description',
            'discount_percentage', 'flat_discount', 'badge_text',
            'is_active', 'valid_from', 'valid_until'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Citizen Express Pass Scheme'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SENIOR50'}),
            'target_audience': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe eligibility and scheme benefits...'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50'}),
            'flat_discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'badge_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50% Subsidy'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SchemeApplicationForm(forms.ModelForm):
    class Meta:
        model = SchemeApplication
        fields = ['applicant_name', 'email', 'phone', 'id_proof_number', 'preferred_route', 'notes']
        widgets = {
            'applicant_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@domain.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'id_proof_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aadhaar / ID Card No'}),
            'preferred_route': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any specific requirements or eligibility details...'}),
        }
