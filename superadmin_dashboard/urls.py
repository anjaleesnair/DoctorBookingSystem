from django.urls import path
from .views import (
    SuperAdminLoginView, SuperAdminLogoutView,
    SuperAdminDashboardView,
    SuperAdminDoctorsView, SuperAdminDoctorEditView, SuperAdminDoctorDeleteView,
    SuperAdminLeavesView, SuperAdminLeaveActionView,
)

urlpatterns = [
    path('login/', SuperAdminLoginView.as_view(), name='superadmin-login'),
    path('logout/', SuperAdminLogoutView.as_view(), name='superadmin-logout'),
    path('dashboard/', SuperAdminDashboardView.as_view(), name='superadmin-dashboard'),
    path('doctors/', SuperAdminDoctorsView.as_view(), name='superadmin-doctors'),
    path('doctors/<int:pk>/edit/', SuperAdminDoctorEditView.as_view(), name='superadmin-doctor-edit'),
    path('doctors/<int:pk>/delete/', SuperAdminDoctorDeleteView.as_view(), name='superadmin-doctor-delete'),
    path('leaves/', SuperAdminLeavesView.as_view(), name='superadmin-leaves'),
    path('leaves/<int:pk>/action/', SuperAdminLeaveActionView.as_view(), name='superadmin-leave-action'),
]
