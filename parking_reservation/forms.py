from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from .models import MyUser, Employee, Department
from django.db import transaction

# ユーザー登録フォーム
class SignupForm(BaseUserCreationForm):
	last_name = forms.CharField(max_length=30)
	first_name = forms.CharField(max_length=30)
	department = forms.ModelChoiceField(queryset=Department.objects.all())
	email = forms.EmailField(required=True)
    
	class Meta:
		model = MyUser
		fields = ['email', 'password1', 'password2']

	def save(self, commit=True):
		user = super().save(commit=False)  # ユーザーをまだ保存しない
		if commit:
			with transaction.atomic():
				user.save()
				Employee.objects.create(
					email = user,
					first_name = self.cleaned_data['first_name'],
					last_name = self.cleaned_data['last_name'],
					department = self.cleaned_data['department'],
				)
		return user



# 登録画面用検索フォーム
class ParkingReservationForm(forms.Form):
	parking_no = forms.IntegerField()
	start_date = forms.DateField()
	end_date = forms.DateField()
	day_division = forms.ChoiceField(choices=[('AM', 'AM'), ('PM', 'PM'), ('終日', '終日')])