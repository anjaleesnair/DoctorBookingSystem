from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsSuperAdmin, IsDoctor, IsCustomer
from .models import Doctor, LeaveRequest, Appointment
from .serializers import (
    DoctorSerializer, DoctorCreateSerializer,
    LeaveRequestSerializer, LeaveRequestCreateSerializer, LeaveApprovalSerializer,
    AppointmentSerializer, BookAppointmentSerializer, SlotSerializer
)
from .utils import generate_slots


# ─────────────────────────────────────────────
# SUPERADMIN — Doctor Management
# ─────────────────────────────────────────────

class DoctorListCreateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        doctors = Doctor.objects.select_related('user').all()
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DoctorCreateSerializer(data=request.data)
        if serializer.is_valid():
            doctor = serializer.save()
            return Response(DoctorSerializer(doctor).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorDetailView(APIView):
    permission_classes = [IsSuperAdmin]

    def get_object(self, pk):
        return get_object_or_404(Doctor, pk=pk)

    def get(self, request, pk):
        doctor = self.get_object(pk)
        return Response(DoctorSerializer(doctor).data)

    def put(self, request, pk):
        doctor = self.get_object(pk)
        serializer = DoctorSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        doctor = self.get_object(pk)
        doctor.user.delete()  # Cascades to doctor
        return Response({'message': 'Doctor deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# SUPERADMIN — Leave Approval
# ─────────────────────────────────────────────

class SuperAdminLeaveListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        leaves = LeaveRequest.objects.select_related('doctor').all().order_by('-created_at')
        serializer = LeaveRequestSerializer(leaves, many=True)
        return Response(serializer.data)


class SuperAdminLeaveApprovalView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if leave.status != 'pending':
            return Response({'error': 'Leave request is already processed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LeaveApprovalSerializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data['action']
            if action == 'approve':
                leave.status = 'approved'
                leave.rejection_reason = None
            else:
                leave.status = 'rejected'
                leave.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            leave.save()
            return Response({
                'message': f'Leave request {leave.status}.',
                'leave': LeaveRequestSerializer(leave).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# SUPERADMIN — View Doctor Slots (Read-only)
# ─────────────────────────────────────────────

class SuperAdminDoctorSlotsView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk)
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date query param is required. (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from datetime import date
            query_date = date.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        slots = generate_slots(doctor, query_date)
        return Response({
            'doctor': DoctorSerializer(doctor).data,
            'date': date_str,
            'slots': SlotSerializer(slots, many=True).data
        })


# ─────────────────────────────────────────────
# DOCTOR — Leave Requests
# ─────────────────────────────────────────────

class DoctorLeaveListCreateView(APIView):
    permission_classes = [IsDoctor]

    def get_doctor(self, user):
        return get_object_or_404(Doctor, user=user)

    def get(self, request):
        doctor = self.get_doctor(request.user)
        leaves = LeaveRequest.objects.filter(doctor=doctor).order_by('-created_at')
        serializer = LeaveRequestSerializer(leaves, many=True)
        return Response(serializer.data)

    def post(self, request):
        doctor = self.get_doctor(request.user)
        serializer = LeaveRequestCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Check if leave already requested for the date
            if LeaveRequest.objects.filter(doctor=doctor, date=serializer.validated_data['date']).exists():
                return Response({'error': 'Leave already requested for this date.'}, status=status.HTTP_400_BAD_REQUEST)
            leave = serializer.save(doctor=doctor)
            return Response(LeaveRequestSerializer(leave).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorAppointmentListView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        doctor = get_object_or_404(Doctor, user=request.user)
        appointments = Appointment.objects.filter(
            doctor=doctor, status='booked'
        ).select_related('customer').order_by('date', 'start_time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────
# CUSTOMER — Doctors, Slots, Booking
# ─────────────────────────────────────────────

class CustomerDoctorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doctors = Doctor.objects.filter(is_active=True)
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data)


class CustomerSlotView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request, pk):
        doctor = get_object_or_404(Doctor, pk=pk, is_active=True)
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date query param is required. (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from datetime import date
            query_date = date.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        slots = generate_slots(doctor, query_date)
        available = [s for s in slots if s['is_available']]
        return Response({
            'doctor': DoctorSerializer(doctor).data,
            'date': date_str,
            'available_slots': SlotSerializer(available, many=True).data
        })


class CustomerBookAppointmentView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = BookAppointmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        doctor_id = serializer.validated_data['doctor_id']
        date = serializer.validated_data['date']
        start_time = serializer.validated_data['start_time']

        doctor = get_object_or_404(Doctor, pk=doctor_id, is_active=True)

        # Use select_for_update inside a transaction to prevent race conditions
        with transaction.atomic():
            # Lock conflicting appointment rows
            conflicting = Appointment.objects.select_for_update().filter(
                doctor=doctor,
                date=date,
                start_time=start_time,
                status='booked'
            )
            if conflicting.exists():
                return Response(
                    {'error': 'This slot is already booked. Please choose another slot.'},
                    status=status.HTTP_409_CONFLICT
                )

            # Validate slot is actually valid (working day, no leave, within hours)
            slots = generate_slots(doctor, date)
            slot_times = [s['start_time'] for s in slots]
            if start_time not in slot_times:
                return Response(
                    {'error': 'Invalid slot. Doctor is unavailable at this time.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate end time
            from datetime import datetime, timedelta
            end_dt = datetime.combine(date, start_time) + timedelta(minutes=doctor.consultation_duration_minutes)
            end_time = end_dt.time()

            appointment = Appointment.objects.create(
                doctor=doctor,
                customer=request.user,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='booked'
            )

        return Response({
            'message': 'Appointment booked successfully.',
            'appointment': AppointmentSerializer(appointment).data
        }, status=status.HTTP_201_CREATED)


class CustomerAppointmentListView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        appointments = Appointment.objects.filter(
            customer=request.user
        ).select_related('doctor').order_by('date', 'start_time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
