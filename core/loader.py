import pandas as pd
from io import StringIO
from .models import Teacher, Group, Course, Room


class DataLoader:
    def __init__(self, db):
        self.db = db

    def load_teachers(self, file):
        content = file.read().decode('utf-8')
        df = pd.read_csv(StringIO(content))

        for _, row in df.iterrows():
            teacher = Teacher(
                id=row['id'],
                name=row['name'],
                max_hours_per_day=row['max_hours_per_day'],
                preferred_days=str(row.get('preferred_days', ''))
            )
            self.db.session.merge(teacher)

    def load_groups(self, file):
        content = file.read().decode('utf-8')
        df = pd.read_csv(StringIO(content))

        for _, row in df.iterrows():
            group = Group(
                id=row['id'],
                name=row['name'],
                size=row['size'],
                max_hours_per_day=row['max_hours_per_day']
            )
            self.db.session.merge(group)

    def load_courses(self, file):
        content = file.read().decode('utf-8')
        df = pd.read_csv(StringIO(content))

        for _, row in df.iterrows():
            course = Course(
                id=row['id'],
                name=row['name'],
                type=row['type'],
                hours_per_week=row['hours_per_week'],
                teacher_id=row['teacher_id'],
                group_id=row['group_id'],
                room_type=row['room_type']
            )
            self.db.session.merge(course)

    def load_rooms(self, file):
        content = file.read().decode('utf-8')
        df = pd.read_csv(StringIO(content))

        for _, row in df.iterrows():
            room = Room(
                id=row['id'],
                name=row['name'],
                capacity=row['capacity'],
                type=row['type'],
                available_hours=str(row['available_hours'])
            )
            self.db.session.merge(room)