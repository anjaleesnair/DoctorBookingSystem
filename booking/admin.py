from django.contrib import admin
from .models import Doctor, LeaveRequest, Appointment

admin.site.register(Doctor)
admin.site.register(LeaveRequest)
admin.site.register(Appointment)
