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

# Home画面用検索フォーム
class SearchForHomeForm(forms.Form):
	search_parking_no = forms.IntegerField(required=False)
	search_start_date = forms.DateField(required=False)
	search_end_date = forms.DateField(required=False)
	use_range = forms.BooleanField(required=False) # 期間検索ON/OFF

	# データの整合性チェックに条件追加
	def clean(self):
		cleaned_data = super().clean()
		search_start_date = cleaned_data.get("search_start_date")
		search_end_date = cleaned_data.get("search_end_date")
		use_range = cleaned_data.get("use_range")
		
		if use_range and (not search_end_date):
			raise forms.ValidationError("期間検索をする場合は終了日を入力してください。")

		if use_range and search_end_date and search_start_date > search_end_date:
			raise forms.ValidationError("開始日は終了日より前にしてください。")

		return cleaned_data

# 登録画面用検索フォーム
class ParkingReservationForm(forms.Form):
	parking_no = forms.IntegerField()
	start_date = forms.DateField()
	end_date = forms.DateField()
	day_division = forms.ChoiceField(choices=[('AM', 'AM'), ('PM', 'PM'), ('終日', '終日')])