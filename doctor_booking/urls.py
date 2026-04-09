from django.urls import path, include

urlpatterns = [
    # Superadmin Custom Dashboard (Template-based, no Django Admin)
    path('superadmin/', include('superadmin_dashboard.urls')),

    # Auth APIs (register, login, token refresh)
    path('api/auth/', include('accounts.urls')),

    # All booking APIs
    path('api/', include('booking.urls')),
]
