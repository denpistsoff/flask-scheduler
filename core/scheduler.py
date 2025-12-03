from datetime import time
from .models import db, Teacher, Group, Course, Room, ScheduleSlot
from app import app


class Scheduler:
    def __init__(self, db):
        self.db = db
        self.timeslots = [
            (time(8, 0), time(9, 30)),
            (time(9, 50), time(11, 20)),
            (time(11, 40), time(13, 10)),
            (time(13, 30), time(15, 0))
        ]

    def generate_schedule(self):
        ScheduleSlot.query.delete()

        courses = Course.query.all()
        rooms = Room.query.all()

        schedule = []
        for day in range(5):
            day_rooms = {room.id: True for room in rooms if self._is_room_available(room, day)}
            day_teachers = {}
            day_groups = {}

            for slot in range(4):
                for course in courses:
                    if course.hours_per_week <= 0:
                        continue

                    if not self._check_teacher_available(course.teacher_id, day, slot, day_teachers):
                        continue

                    if not self._check_group_available(course.group_id, day, slot, day_groups):
                        continue

                    room = self._find_available_room(course.room_type, day, slot, day_rooms)
                    if not room:
                        continue

                    schedule_slot = self._create_slot(course, day, slot, room.id)
                    schedule.append(schedule_slot)

                    course.hours_per_week -= 1
                    day_teachers[course.teacher_id] = True
                    day_groups[course.group_id] = True
                    day_rooms[room.id] = False

        self.db.session.add_all(schedule)
        self.db.session.commit()
        return schedule

    def _is_room_available(self, room, day):
        if not room.available_hours:
            return True
        hours = room.available_hours.split(',')
        return day < len(hours) and hours[day] != '0'

    def _check_teacher_available(self, teacher_id, day, slot, busy_teachers):
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return False
        if teacher_id in busy_teachers:
            return False
        if teacher.preferred_days and str(day + 1) not in teacher.preferred_days.split(','):
            return False
        return True

    def _check_group_available(self, group_id, day, slot, busy_groups):
        if group_id in busy_groups:
            return False
        group = Group.query.get(group_id)
        return group and group.max_hours_per_day > 0

    def _find_available_room(self, room_type, day, slot, available_rooms):
        rooms = Room.query.filter_by(type=room_type).all()
        for room in rooms:
            if room.id in available_rooms and available_rooms[room.id]:
                return room
        return None

    def _create_slot(self, course, day, slot, room_id):
        start, end = self.timeslots[slot]
        return ScheduleSlot(
            day=day,
            slot=slot,
            start_time=start,
            end_time=end,
            course_id=course.id,
            teacher_id=course.teacher_id,
            group_id=course.group_id,
            room_id=room_id
        )

    def get_statistics(self):
        return {
            'total_slots': ScheduleSlot.query.count(),
            'teachers': Teacher.query.count(),
            'groups': Group.query.count(),
            'courses': Course.query.count(),
            'rooms': Room.query.count()
        }