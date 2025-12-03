from app import db
from datetime import time


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    max_hours_per_day = db.Column(db.Integer, default=4)
    preferred_days = db.Column(db.String(50), default='')  # "1,2,4" = Пн,Вт,Чт

    courses = db.relationship('Course', backref='teacher', lazy=True)
    schedule_slots = db.relationship('ScheduleSlot', backref='teacher', lazy=True)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    max_hours_per_day = db.Column(db.Integer, default=6)

    courses = db.relationship('Course', backref='group', lazy=True)
    schedule_slots = db.relationship('ScheduleSlot', backref='group', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # lecture, practice, lab
    hours_per_week = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)

    schedule_slots = db.relationship('ScheduleSlot', backref='course', lazy=True)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # lecture_hall, computer_class
    available_hours = db.Column(db.String(100), default='')  # "1-8,1-8,1-8,1-8,1-6"

    schedule_slots = db.relationship('ScheduleSlot', backref='room', lazy=True)


class ScheduleSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)  # 0-4 = Пн-Пт
    slot = db.Column(db.Integer, nullable=False)  # 0-3 = 1-4 пара
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('day', 'slot', 'teacher_id', name='_teacher_time_uc'),
        db.UniqueConstraint('day', 'slot', 'group_id', name='_group_time_uc'),
        db.UniqueConstraint('day', 'slot', 'room_id', name='_room_time_uc'),
    )