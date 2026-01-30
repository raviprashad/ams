# timetable/utils.py

import datetime
from .models import LectureSlot, ScheduledLecture

def generate_today_scheduled_lectures():
    today = datetime.date.today()
    weekday = today.strftime('%A')  # E.g. 'Monday'

    slots_today = LectureSlot.objects.filter(day_of_week=weekday)

    for slot in slots_today:
        ScheduledLecture.objects.get_or_create(
            slot=slot,
            date=today,
            defaults={
                'subject': slot.subject,
                'teacher': slot.teacher,
                'lecture_number': slot.lecture_number
            }
        )
