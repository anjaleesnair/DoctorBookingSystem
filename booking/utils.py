from datetime import datetime, timedelta
from .models import LeaveRequest, Appointment


def generate_slots(doctor, date):
    """
    Dynamically generate time slots for a doctor on a given date.
    Does NOT store slots in DB — generated on the fly.
    """
    # Check if this day is a working day for the doctor
    day_name = date.strftime('%A').lower()
    if day_name not in doctor.working_days:
        return []

    # Check if doctor has an approved leave on this date
    has_leave = LeaveRequest.objects.filter(
        doctor=doctor,
        date=date,
        status='approved'
    ).exists()
    if has_leave:
        return []

    # Get already booked slots for this doctor on this date
    booked_times = set(
        Appointment.objects.filter(
            doctor=doctor,
            date=date,
            status='booked'
        ).values_list('start_time', flat=True)
    )

    # Generate slots
    slots = []
    slot_duration = timedelta(minutes=doctor.consultation_duration_minutes)
    current = datetime.combine(date, doctor.start_time)
    end = datetime.combine(date, doctor.end_time)
    max_slots = doctor.consultations_per_day
    count = 0

    while current + slot_duration <= end and count < max_slots:
        slot_start = current.time()
        slot_end = (current + slot_duration).time()
        is_available = slot_start not in booked_times

        slots.append({
            'start_time': slot_start,
            'end_time': slot_end,
            'is_available': is_available
        })
        current += slot_duration
        count += 1

    return slots
