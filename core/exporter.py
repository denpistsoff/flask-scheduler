from datetime import time


class HTMLExporter:
    def __init__(self):
        self.days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
        self.slots = [
            '8:00-9:30',
            '9:50-11:20',
            '11:40-13:10',
            '13:30-15:00'
        ]

    def export(self, schedule):
        html = '''
        <div class="schedule-container">
            <h2>Расписание занятий</h2>
            <table class="schedule-table">
                <thead>
                    <tr>
                        <th>Время</th>
        '''

        for day in self.days:
            html += f'<th>{day}</th>'

        html += '</tr></thead><tbody>'

        for slot_idx in range(4):
            html += f'<tr><td class="time-slot">{self.slots[slot_idx]}</td>'

            for day_idx in range(5):
                cell_html = '<td class="schedule-cell">'

                for slot in schedule:
                    if slot.day == day_idx and slot.slot == slot_idx:
                        cell_html += f'''
                        <div class="course-card">
                            <div class="course-name">{slot.course.name}</div>
                            <div class="course-type">{slot.course.type}</div>
                            <div class="teacher">{slot.teacher.name}</div>
                            <div class="room">{slot.room.name}</div>
                            <div class="group">{slot.group.name}</div>
                        </div>
                        '''

                if '</div>' not in cell_html:
                    cell_html += '<div class="empty-slot">—</div>'

                cell_html += '</td>'
                html += cell_html

            html += '</tr>'

        html += '</tbody></table></div>'
        return html