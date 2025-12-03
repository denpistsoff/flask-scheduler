from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Конфигурация для PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://scheduler_user:ваш_пароль@localhost/scheduler_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ваш-секретный-ключ-для-продакшена')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему'
login_manager.login_message_category = 'warning'


# --- Модели ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    teachers = db.relationship('Teacher', backref='user', lazy=True, cascade='all, delete-orphan')
    groups = db.relationship('Group', backref='user', lazy=True, cascade='all, delete-orphan')
    rooms = db.relationship('Room', backref='user', lazy=True, cascade='all, delete-orphan')
    courses = db.relationship('Course', backref='user', lazy=True, cascade='all, delete-orphan')
    schedule_slots = db.relationship('ScheduleSlot', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    max_hours = db.Column(db.Integer, default=4)
    preferred_days = db.Column(db.String(50), default="")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'max_hours': self.max_hours,
            'preferred_days': self.preferred_days
        }


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, default=25)
    max_hours = db.Column(db.Integer, default=6)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'size': self.size,
            'max_hours': self.max_hours
        }


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=30)
    type = db.Column(db.String(20), default="lecture_hall")
    schedule = db.Column(db.String(100), default="1111111,1111111,1111111,1111111,1111111")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'capacity': self.capacity,
            'type': self.type,
            'schedule': self.schedule
        }


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), default="lecture")
    hours = db.Column(db.Integer, default=2)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    room_type = db.Column(db.String(20), default="lecture_hall")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    teacher = db.relationship('Teacher', backref='courses')
    group = db.relationship('Group', backref='courses')

    def to_dict(self):
        teacher = Teacher.query.get(self.teacher_id)
        group = Group.query.get(self.group_id)

        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'hours': self.hours,
            'teacher_id': self.teacher_id,
            'group_id': self.group_id,
            'room_type': self.room_type,
            'teacher_name': teacher.name if teacher else None,
            'group_name': group.name if group else None
        }


class ScheduleSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    slot = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    course = db.relationship('Course')
    teacher = db.relationship('Teacher')
    group = db.relationship('Group')
    room = db.relationship('Room')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Вспомогательные функции ---
def create_timeslots():
    return [
        {"time": "07:30 - 08:30", "start": "07:30", "end": "08:30"},
        {"time": "08:30 - 10:00", "start": "08:30", "end": "10:00"},
        {"time": "10:10 - 11:40", "start": "10:10", "end": "11:40"},
        {"time": "11:50 - 13:20", "start": "11:50", "end": "13:20"},
        {"time": "13:40 - 15:10", "start": "13:40", "end": "15:10"},
        {"time": "15:20 - 16:50", "start": "15:20", "end": "16:50"},
        {"time": "17:00 - 18:30", "start": "17:00", "end": "18:30"}
    ]


def get_day_name(day_index):
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    return days[day_index] if 0 <= day_index < len(days) else f"День {day_index + 1}"


# --- Маршруты аутентификации ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- Основные маршруты (требуют авторизации) ---
@app.route('/')
@login_required
def index():
    try:
        stats = {
            'teachers': Teacher.query.filter_by(user_id=current_user.id).count(),
            'groups': Group.query.filter_by(user_id=current_user.id).count(),
            'courses': Course.query.filter_by(user_id=current_user.id).count(),
            'rooms': Room.query.filter_by(user_id=current_user.id).count(),
            'scheduled': ScheduleSlot.query.filter_by(user_id=current_user.id).count()
        }
        return render_template('index.html', stats=stats)
    except:
        stats = {'teachers': 0, 'groups': 0, 'courses': 0, 'rooms': 0, 'scheduled': 0}
        return render_template('index.html', stats=stats)


@app.route('/setup')
@login_required
def setup():
    return render_template('setup.html')


@app.route('/manage')
@login_required
def manage():
    return render_template('manage.html')


@app.route('/schedule')
@login_required
def schedule():
    return render_template('schedule.html')


# --- API (требуют авторизации) ---
@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        stats = {
            'success': True,
            'teachers': Teacher.query.filter_by(user_id=current_user.id).count(),
            'groups': Group.query.filter_by(user_id=current_user.id).count(),
            'courses': Course.query.filter_by(user_id=current_user.id).count(),
            'rooms': Room.query.filter_by(user_id=current_user.id).count(),
            'scheduled': ScheduleSlot.query.filter_by(user_id=current_user.id).count()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- API для преподавателей ---
@app.route('/api/teachers', methods=['GET', 'POST'])
@login_required
def handle_teachers():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if 'id' in data:
                teacher = Teacher.query.filter_by(id=data['id'], user_id=current_user.id).first()
                if teacher:
                    teacher.name = data.get('name', teacher.name)
                    teacher.max_hours = data.get('max_hours', teacher.max_hours)
                    teacher.preferred_days = data.get('preferred_days', teacher.preferred_days)
            else:
                teacher = Teacher(
                    name=data.get('name', ''),
                    max_hours=data.get('max_hours', 4),
                    preferred_days=data.get('preferred_days', ''),
                    user_id=current_user.id
                )
                db.session.add(teacher)

            db.session.commit()
            return jsonify({"success": True})

        teachers = Teacher.query.filter_by(user_id=current_user.id).all()
        return jsonify([t.to_dict() for t in teachers])
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/teachers/<int:id>', methods=['DELETE'])
@login_required
def delete_teacher(id):
    try:
        teacher = Teacher.query.filter_by(id=id, user_id=current_user.id).first()
        if teacher:
            db.session.delete(teacher)
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- API для групп ---
@app.route('/api/groups', methods=['GET', 'POST'])
@login_required
def handle_groups():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if 'id' in data:
                group = Group.query.filter_by(id=data['id'], user_id=current_user.id).first()
                if group:
                    group.name = data.get('name', group.name)
                    group.size = data.get('size', group.size)
                    group.max_hours = data.get('max_hours', group.max_hours)
            else:
                group = Group(
                    name=data.get('name', ''),
                    size=data.get('size', 25),
                    max_hours=data.get('max_hours', 6),
                    user_id=current_user.id
                )
                db.session.add(group)

            db.session.commit()
            return jsonify({"success": True})

        groups = Group.query.filter_by(user_id=current_user.id).all()
        return jsonify([g.to_dict() for g in groups])
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/groups/<int:id>', methods=['DELETE'])
@login_required
def delete_group(id):
    try:
        group = Group.query.filter_by(id=id, user_id=current_user.id).first()
        if group:
            db.session.delete(group)
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- API для аудиторий ---
@app.route('/api/rooms', methods=['GET', 'POST'])
@login_required
def handle_rooms():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if 'id' in data:
                room = Room.query.filter_by(id=data['id'], user_id=current_user.id).first()
                if room:
                    room.name = data.get('name', room.name)
                    room.capacity = data.get('capacity', room.capacity)
                    room.type = data.get('type', room.type)
                    room.schedule = data.get('schedule', room.schedule)
            else:
                room = Room(
                    name=data.get('name', ''),
                    capacity=data.get('capacity', 30),
                    type=data.get('type', 'lecture_hall'),
                    schedule=data.get('schedule', '1111111,1111111,1111111,1111111,1111111'),
                    user_id=current_user.id
                )
                db.session.add(room)

            db.session.commit()
            return jsonify({"success": True})

        rooms = Room.query.filter_by(user_id=current_user.id).all()
        return jsonify([r.to_dict() for r in rooms])
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/rooms/<int:id>', methods=['DELETE'])
@login_required
def delete_room(id):
    try:
        room = Room.query.filter_by(id=id, user_id=current_user.id).first()
        if room:
            db.session.delete(room)
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- API для курсов ---
@app.route('/api/courses', methods=['GET', 'POST'])
@login_required
def handle_courses():
    try:
        if request.method == 'POST':
            data = request.get_json()

            if 'id' in data:
                course = Course.query.filter_by(id=data['id'], user_id=current_user.id).first()
                if course:
                    course.name = data.get('name', course.name)
                    course.type = data.get('type', course.type)
                    course.hours = int(data.get('hours', 2))
                    course.teacher_id = int(data.get('teacher_id', 0))
                    course.group_id = int(data.get('group_id', 0))
                    course.room_type = data.get('room_type', 'lecture_hall')
            else:
                course = Course(
                    name=data.get('name', ''),
                    type=data.get('type', 'lecture'),
                    hours=int(data.get('hours', 2)),
                    teacher_id=int(data.get('teacher_id', 0)),
                    group_id=int(data.get('group_id', 0)),
                    room_type=data.get('room_type', 'lecture_hall'),
                    user_id=current_user.id
                )
                db.session.add(course)

            db.session.commit()
            return jsonify({"success": True})

        courses = Course.query.filter_by(user_id=current_user.id).all()
        return jsonify([c.to_dict() for c in courses])
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/courses/<int:id>', methods=['DELETE'])
@login_required
def delete_course(id):
    try:
        course = Course.query.filter_by(id=id, user_id=current_user.id).first()
        if course:
            db.session.delete(course)
            db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- API для расписания ---
@app.route('/api/schedule', methods=['GET'])
@login_required
def get_schedule():
    try:
        slots = ScheduleSlot.query.filter_by(user_id=current_user.id).all()
        timeslots = create_timeslots()

        schedule_data = {
            'success': True,
            'total_slots': len(slots),
            'days': [
                {'name': 'Понедельник', 'index': 0, 'slots': [[] for _ in range(7)]},
                {'name': 'Вторник', 'index': 1, 'slots': [[] for _ in range(7)]},
                {'name': 'Среда', 'index': 2, 'slots': [[] for _ in range(7)]},
                {'name': 'Четверг', 'index': 3, 'slots': [[] for _ in range(7)]},
                {'name': 'Пятница', 'index': 4, 'slots': [[] for _ in range(7)]}
            ],
            'timeslots': timeslots
        }

        for slot in slots:
            if 0 <= slot.day < 5 and 0 <= slot.slot < 7:
                course = Course.query.filter_by(id=slot.course_id,
                                                user_id=current_user.id).first() if slot.course_id else None
                teacher = Teacher.query.filter_by(id=slot.teacher_id,
                                                  user_id=current_user.id).first() if slot.teacher_id else None
                group = Group.query.filter_by(id=slot.group_id,
                                              user_id=current_user.id).first() if slot.group_id else None
                room = Room.query.filter_by(id=slot.room_id, user_id=current_user.id).first() if slot.room_id else None

                schedule_data['days'][slot.day]['slots'][slot.slot].append({
                    'course': course.to_dict() if course else None,
                    'teacher': teacher.to_dict() if teacher else None,
                    'group': group.to_dict() if group else None,
                    'room': room.to_dict() if room else None
                })

        return jsonify(schedule_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Генерация расписания ---
@app.route('/api/generate-schedule', methods=['POST'])
@login_required
def generate_schedule():
    try:
        # Удаляем старые слоты текущего пользователя
        ScheduleSlot.query.filter_by(user_id=current_user.id).delete()

        courses = Course.query.filter_by(user_id=current_user.id).all()
        rooms = Room.query.filter_by(user_id=current_user.id).all()
        teachers = Teacher.query.filter_by(user_id=current_user.id).all()
        groups = Group.query.filter_by(user_id=current_user.id).all()

        if not courses:
            return jsonify({'success': False, 'error': 'Нет курсов для расписания'}), 400

        slots_created = 0
        MAX_ATTEMPTS = 200  # Увеличим количество попыток

        for course in courses:
            hours_placed = 0
            attempts = 0

            # Получаем предпочитаемые дни преподавателя
            teacher = Teacher.query.filter_by(id=course.teacher_id, user_id=current_user.id).first()
            preferred_days = []
            if teacher and teacher.preferred_days:
                preferred_days = [int(d.strip()) for d in teacher.preferred_days.split(',') if d.strip()]

            # Если нет предпочитаемых дней, используем все рабочие дни (1-5)
            if not preferred_days:
                preferred_days = [1, 2, 3, 4, 5]

            # Приводим к индексам 0-4
            preferred_day_indices = [d - 1 for d in preferred_days if 1 <= d <= 5]

            while hours_placed < course.hours and attempts < MAX_ATTEMPTS:
                attempts += 1

                # Пробуем сначала предпочитаемые дни
                for day_index in preferred_day_indices:
                    if hours_placed >= course.hours:
                        break

                    # Пробуем разные временные слоты
                    slot_order = list(range(7))
                    # Можно добавить предпочитаемые слоты если нужно

                    for slot in slot_order:
                        if hours_placed >= course.hours:
                            break

                        # Проверяем доступность преподавателя
                        teacher_busy = ScheduleSlot.query.filter_by(
                            day=day_index, slot=slot, teacher_id=course.teacher_id, user_id=current_user.id
                        ).first()

                        if teacher_busy:
                            continue

                        # Проверяем доступность группы
                        group_busy = ScheduleSlot.query.filter_by(
                            day=day_index, slot=slot, group_id=course.group_id, user_id=current_user.id
                        ).first()

                        if group_busy:
                            continue

                        # Ищем подходящую аудиторию
                        suitable_room = None
                        for room in rooms:
                            if room.type == course.room_type:
                                schedule_days = room.schedule.split(',')
                                if day_index < len(schedule_days) and slot < len(schedule_days[day_index]):
                                    if schedule_days[day_index][slot] == '1':
                                        # Проверяем, не занята ли аудитория
                                        room_busy = ScheduleSlot.query.filter_by(
                                            day=day_index, slot=slot, room_id=room.id, user_id=current_user.id
                                        ).first()

                                        if not room_busy:
                                            suitable_room = room
                                            break

                        if suitable_room:
                            # Создаем слот расписания
                            schedule_slot = ScheduleSlot(
                                day=day_index,
                                slot=slot,
                                course_id=course.id,
                                teacher_id=course.teacher_id,
                                group_id=course.group_id,
                                room_id=suitable_room.id,
                                user_id=current_user.id
                            )
                            db.session.add(schedule_slot)
                            slots_created += 1
                            hours_placed += 1
                            break  # Переходим к следующему часу курса

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Расписание создано! Запланировано {slots_created} занятий',
            'slots_created': slots_created,
            'total_courses': len(courses)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Очистка расписания ---
@app.route('/api/clear-schedule', methods=['POST'])
@login_required
def clear_schedule():
    try:
        ScheduleSlot.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Расписание очищено'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Старая совместимость ---
@app.route('/api/generate', methods=['POST'])
@login_required
def generate():
    return generate_schedule()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создание администратора если его нет
        if User.query.filter_by(username='admin').first() is None:
            admin = User(username='admin', email='admin@scheduler.ru', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    app.run(host='0.0.0.0', port=5000)