from django.contrib import admin
from .models import Department, MyUser, Employee, ParkingReservation, ParkingFeeModel

# Register your models here.
admin.site.register(Department)
admin.site.register(MyUser)
admin.site.register(Employee)
admin.site.register(ParkingReservation)
admin.site.register(ParkingFeeModel)
