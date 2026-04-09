from rest_framework import serializers
from .models import Doctor, LeaveRequest, Appointment
from accounts.models import User


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'specialization', 'consultation_duration_minutes',
            'consultations_per_day', 'start_time', 'end_time', 'working_days', 'is_active'
        ]


class DoctorCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Doctor
        fields = [
            'username', 'password', 'email',
            'name', 'specialization', 'consultation_duration_minutes',
            'consultations_per_day', 'start_time', 'end_time', 'working_days'
        ]

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email = validated_data.pop('email', '')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role='doctor'
        )
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor


class LeaveRequestSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ['id', 'doctor', 'doctor_name', 'date', 'reason', 'status', 'rejection_reason', 'created_at']
        read_only_fields = ['doctor', 'status', 'rejection_reason', 'created_at']


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['date', 'reason']

    def validate_date(self, value):
        from django.utils import timezone
        if value <= timezone.now().date():
            raise serializers.ValidationError("Leave date must be in the future.")
        return value


class LeaveApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rejection reason is required."})
        return data


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'doctor_name', 'customer', 'customer_name',
                  'date', 'start_time', 'end_time', 'status', 'created_at']
        read_only_fields = ['customer', 'end_time', 'status', 'created_at']


class BookAppointmentSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()

    def validate(self, data):
        from django.utils import timezone
        if data['date'] < timezone.now().date():
            raise serializers.ValidationError({"date": "Cannot book appointments in the past."})
        return data


class SlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_available = serializers.BooleanField()
