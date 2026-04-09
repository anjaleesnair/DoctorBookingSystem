from django.urls import path
from .views import (
    # Superadmin
    DoctorListCreateView, DoctorDetailView,
    SuperAdminLeaveListView, SuperAdminLeaveApprovalView,
    SuperAdminDoctorSlotsView,
    # Doctor
    DoctorLeaveListCreateView, DoctorAppointmentListView,
    # Customer
    CustomerDoctorListView, CustomerSlotView,
    CustomerBookAppointmentView, CustomerAppointmentListView,
)

urlpatterns = [
    # ── Superadmin ──────────────────────────────
    path('admin/doctors/', DoctorListCreateView.as_view(), name='admin-doctor-list-create'),
    path('admin/doctors/<int:pk>/', DoctorDetailView.as_view(), name='admin-doctor-detail'),
    path('admin/leaves/', SuperAdminLeaveListView.as_view(), name='admin-leave-list'),
    path('admin/leaves/<int:pk>/action/', SuperAdminLeaveApprovalView.as_view(), name='admin-leave-action'),
    path('admin/doctors/<int:pk>/slots/', SuperAdminDoctorSlotsView.as_view(), name='admin-doctor-slots'),

    # ── Doctor ───────────────────────────────────
    path('doctor/leaves/', DoctorLeaveListCreateView.as_view(), name='doctor-leave'),
    path('doctor/appointments/', DoctorAppointmentListView.as_view(), name='doctor-appointments'),

    # ── Customer ─────────────────────────────────
    path('doctors/', CustomerDoctorListView.as_view(), name='customer-doctors'),
    path('doctors/<int:pk>/slots/', CustomerSlotView.as_view(), name='customer-slots'),
    path('appointments/book/', CustomerBookAppointmentView.as_view(), name='book-appointment'),
    path('appointments/', CustomerAppointmentListView.as_view(), name='customer-appointments'),
]
