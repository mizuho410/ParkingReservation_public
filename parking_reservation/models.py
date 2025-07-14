from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# 部署管理用
class Department(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

# カスタムマネージャの定義
class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('The Email field must be set')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):

        user = self.create_user(
            email,
            password=password,
        )
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

# カスタムユーザーモデル    
class MyUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    objects = MyUserManager()

    def __str__(self):
        return self.email
    
    # ログインユーザーのフルネーム取得用処理
    def get_full_name(self):
        employee = self.employee # リレーションの逆参照
        return f"{employee.last_name}{employee.first_name}"

# 従業員管理用
class Employee(models.Model):
    email = models.OneToOneField(MyUser,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return f'{self.last_name} {self.first_name} ({self.email.email})'

# 駐車場予約管理用
from django.db import models

class ParkingReservation(models.Model):
    parking_no = models.IntegerField()
    reservation_holder = models.CharField(max_length=100)
    date = models.DateField()

    class DivisionChoices(models.TextChoices):
        AM = 'AM', 'AM'
        PM = 'PM', 'PM'
        ALL = '終日', '終日'

    day_division = models.CharField(
        max_length=10,
        choices=DivisionChoices.choices,
        default=DivisionChoices.ALL
    )

    def __str__(self):
        return str(self.parking_no)

# 駐車場料金管理用
class ParkingFeeModel(models.Model):
    parking_fee = models.IntegerField()
