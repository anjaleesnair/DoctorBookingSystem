import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from booking.models import Doctor, LeaveRequest, Appointment
from accounts.models import User


def superadmin_required(view_func):
    """Decorator to restrict access to superadmin role only."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'superadmin':
            return redirect('superadmin-login')
        return view_func(request, *args, **kwargs)
    return wrapper


class SuperAdminLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.role == 'superadmin':
            return redirect('superadmin-dashboard')
        return render(request, 'superadmin/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'superadmin':
            login(request, user)
            return redirect('superadmin-dashboard')
        return render(request, 'superadmin/login.html', {'error': 'Invalid credentials or not a superadmin.'})


class SuperAdminLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('superadmin-login')


@method_decorator(superadmin_required, name='dispatch')
class SuperAdminDashboardView(View):
    def get(self, request):
        context = {
            'total_doctors': Doctor.objects.count(),
            'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
            'total_appointments': Appointment.objects.filter(status='booked').count(),
            'recent_leaves': LeaveRequest.objects.select_related('doctor').order_by('-created_at')[:5],
        }
        return render(request, 'superadmin/dashboard.html', context)


DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


@method_decorator(superadmin_required, name='dispatch')
class SuperAdminDoctorsView(View):
    def get(self, request):
        doctors = Doctor.objects.select_related('user').all()
        return render(request, 'superadmin/doctors.html', {'doctors': doctors, 'days': DAYS})

    def post(self, request):
        action = request.POST.get('action')
        if action == 'create':
            working_days = request.POST.getlist('working_days')
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password'],
                    role='doctor'
                )
                Doctor.objects.create(
                    user=user,
                    name=request.POST['name'],
                    specialization=request.POST['specialization'],
                    start_time=request.POST['start_time'],
                    end_time=request.POST['end_time'],
                    consultation_duration_minutes=int(request.POST['consultation_duration_minutes']),
                    consultations_per_day=int(request.POST['consultations_per_day']),
                    working_days=working_days,
                )
                messages.success(request, 'Doctor created successfully.')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return redirect('superadmin-doctors')


@method_decorator(superadmin_required, name='dispatch')
class SuperAdminDoctorEditView(View):
    def get(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        return render(request, 'superadmin/doctors.html', {
            'doctors': Doctor.objects.all(),
            'days': DAYS,
            'edit_doctor': doctor
        })

    def post(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        working_days = request.POST.getlist('working_days')
        doctor.name = request.POST.get('name', doctor.name)
        doctor.specialization = request.POST.get('specialization', doctor.specialization)
        doctor.start_time = request.POST.get('start_time', doctor.start_time)
        doctor.end_time = request.POST.get('end_time', doctor.end_time)
        doctor.consultation_duration_minutes = int(request.POST.get('consultation_duration_minutes', doctor.consultation_duration_minutes))
        doctor.consultations_per_day = int(request.POST.get('consultations_per_day', doctor.consultations_per_day))
        if working_days:
            doctor.working_days = working_days
        doctor.save()
        messages.success(request, 'Doctor updated successfully.')
        return redirect('superadmin-doctors')


@method_decorator(superadmin_required, name='dispatch')
class SuperAdminDoctorDeleteView(View):
    def post(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        doctor.user.delete()
        messages.success(request, 'Doctor deleted successfully.')
        return redirect('superadmin-doctors')


@method_decorator(superadmin_required, name='dispatch')
class SuperAdminLeavesView(View):
    def get(self, request):
        leaves = LeaveRequest.objects.select_related('doctor').order_by('-created_at')
        return render(request, 'superadmin/leaves.html', {'leaves': leaves})


@method_decorator(superadmin_required, name='dispatch')
class SuperAdminLeaveActionView(View):
    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        action = request.POST.get('action')
        if leave.status != 'pending':
            messages.error(request, 'Leave request already processed.')
            return redirect('superadmin-leaves')

        if action == 'approve':
            leave.status = 'approved'
            leave.rejection_reason = None
            messages.success(request, f"Leave for {leave.doctor.name} on {leave.date} approved.")
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('superadmin-leaves')
            leave.status = 'rejected'
            leave.rejection_reason = rejection_reason
            messages.success(request, f"Leave for {leave.doctor.name} on {leave.date} rejected.")
        leave.save()
        return redirect('superadmin-leaves')
