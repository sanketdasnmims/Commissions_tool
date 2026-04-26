from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///choreboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def now():
    """Return current UTC time as a naive datetime (consistent with DB storage)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Models ──────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    avatar_color = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'avatar_color': self.avatar_color}


class Chore(db.Model):
    __tablename__ = 'chores'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    frequency = db.Column(db.String(50), default='once')
    due_date = db.Column(db.Date)
    estimated_effort = db.Column(db.Integer, default=1)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    parent_chore_id = db.Column(db.Integer, db.ForeignKey('chores.id'), nullable=True)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    user = db.relationship('User', foreign_keys=[assigned_to])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'assigned_user': self.user.to_dict() if self.user else None,
            'frequency': self.frequency,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_effort': self.estimated_effort,
            'priority': self.priority,
            'status': self.status,
            'notes': self.notes,
            'parent_chore_id': self.parent_chore_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ChoreHistory(db.Model):
    __tablename__ = 'chore_history'
    id = db.Column(db.Integer, primary_key=True)
    original_chore_id = db.Column(db.Integer, db.ForeignKey('chores.id'), nullable=True)
    chore_title = db.Column(db.String(200), nullable=False)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=now)
    effort_points = db.Column(db.Integer, default=1)
    category = db.Column(db.String(50))

    user = db.relationship('User', foreign_keys=[completed_by])

    def to_dict(self):
        return {
            'id': self.id,
            'original_chore_id': self.original_chore_id,
            'chore_title': self.chore_title,
            'completed_by': self.completed_by,
            'completed_by_name': self.user.name if self.user else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'effort_points': self.effort_points,
            'category': self.category,
        }


# ── Seed Data ────────────────────────────────────────────────────────────────

def seed_data():
    if User.query.count() > 0:
        return

    alex = User(name='Alex', avatar_color='#6366f1')
    jordan = User(name='Jordan', avatar_color='#f59e0b')
    db.session.add_all([alex, jordan])
    db.session.flush()

    today = date.today()

    chores_data = [
        dict(title='Wash dishes', category='Kitchen', assigned_to=alex.id, frequency='daily',
             due_date=today, estimated_effort=2, priority='high', status='pending'),
        dict(title='Wipe down counters', category='Kitchen', assigned_to=jordan.id, frequency='daily',
             due_date=today, estimated_effort=1, priority='medium', status='pending'),
        dict(title='Empty dishwasher', category='Kitchen', assigned_to=alex.id, frequency='daily',
             due_date=today - timedelta(days=1), estimated_effort=1, priority='medium', status='pending'),
        dict(title='Clean stovetop', category='Kitchen', assigned_to=jordan.id, frequency='weekly',
             due_date=today - timedelta(days=2), estimated_effort=2, priority='medium', status='pending'),
        dict(title='Mop kitchen floor', category='Kitchen', assigned_to=alex.id, frequency='weekly',
             due_date=today + timedelta(days=3), estimated_effort=3, priority='low', status='pending'),
        dict(title='Clean microwave', category='Kitchen', assigned_to=jordan.id, frequency='biweekly',
             due_date=today + timedelta(days=5), estimated_effort=2, priority='low', status='pending'),
        dict(title='Deep clean oven', category='Kitchen', assigned_to=None, frequency='monthly',
             due_date=today + timedelta(days=14), estimated_effort=4, priority='low', status='pending'),
        dict(title='Vacuum living room', category='Cleaning', assigned_to=jordan.id, frequency='weekly',
             due_date=today, estimated_effort=2, priority='medium', status='pending'),
        dict(title='Vacuum bedrooms', category='Cleaning', assigned_to=alex.id, frequency='weekly',
             due_date=today - timedelta(days=3), estimated_effort=2, priority='medium', status='pending'),
        dict(title='Clean bathrooms', category='Cleaning', assigned_to=jordan.id, frequency='weekly',
             due_date=today - timedelta(days=1), estimated_effort=3, priority='high', status='pending'),
        dict(title='Dust surfaces', category='Cleaning', assigned_to=alex.id, frequency='weekly',
             due_date=today + timedelta(days=2), estimated_effort=2, priority='low', status='pending'),
        dict(title='Mop hallway', category='Cleaning', assigned_to=jordan.id, frequency='weekly',
             due_date=today + timedelta(days=4), estimated_effort=2, priority='low', status='pending'),
        dict(title='Clean windows', category='Cleaning', assigned_to=None, frequency='monthly',
             due_date=today + timedelta(days=10), estimated_effort=4, priority='low', status='pending'),
        dict(title='Scrub shower tiles', category='Cleaning', assigned_to=alex.id, frequency='biweekly',
             due_date=today - timedelta(days=4), estimated_effort=3, priority='medium', status='pending'),
        dict(title='Do laundry', category='Laundry', assigned_to=alex.id, frequency='weekly',
             due_date=today, estimated_effort=2, priority='high', status='in-progress'),
        dict(title='Fold and put away clothes', category='Laundry', assigned_to=jordan.id, frequency='weekly',
             due_date=today + timedelta(days=1), estimated_effort=2, priority='medium', status='pending'),
        dict(title='Change bed sheets', category='Laundry', assigned_to=alex.id, frequency='biweekly',
             due_date=today + timedelta(days=6), estimated_effort=3, priority='medium', status='pending'),
        dict(title='Wash towels', category='Laundry', assigned_to=jordan.id, frequency='weekly',
             due_date=today - timedelta(days=2), estimated_effort=2, priority='medium', status='pending'),
        dict(title='Take out trash', category='Outdoor', assigned_to=jordan.id, frequency='weekly',
             due_date=today, estimated_effort=1, priority='high', status='pending'),
        dict(title='Recycling bins', category='Outdoor', assigned_to=alex.id, frequency='weekly',
             due_date=today + timedelta(days=1), estimated_effort=1, priority='medium', status='pending'),
        dict(title='Mow lawn', category='Outdoor', assigned_to=None, frequency='weekly',
             due_date=today + timedelta(days=3), estimated_effort=4, priority='medium', status='pending'),
        dict(title='Water plants', category='Outdoor', assigned_to=jordan.id, frequency='daily',
             due_date=today, estimated_effort=1, priority='medium', status='pending'),
        dict(title='Sweep porch', category='Outdoor', assigned_to=alex.id, frequency='weekly',
             due_date=today + timedelta(days=5), estimated_effort=2, priority='low', status='pending'),
        dict(title='Grocery shopping', category='Errands', assigned_to=jordan.id, frequency='weekly',
             due_date=today + timedelta(days=2), estimated_effort=3, priority='high', status='pending'),
        dict(title='Pick up dry cleaning', category='Errands', assigned_to=alex.id, frequency='once',
             due_date=today - timedelta(days=5), estimated_effort=1, priority='medium', status='pending'),
        dict(title='Pharmacy run', category='Errands', assigned_to=jordan.id, frequency='once',
             due_date=today + timedelta(days=4), estimated_effort=1, priority='medium', status='pending'),
        dict(title='Replace HVAC filter', category='Maintenance', assigned_to=alex.id, frequency='monthly',
             due_date=today - timedelta(days=7), estimated_effort=2, priority='high', status='pending'),
        dict(title='Test smoke detectors', category='Maintenance', assigned_to=None, frequency='monthly',
             due_date=today + timedelta(days=20), estimated_effort=1, priority='high', status='pending'),
        dict(title='Water softener salt', category='Maintenance', assigned_to=jordan.id, frequency='monthly',
             due_date=today + timedelta(days=8), estimated_effort=2, priority='medium', status='pending'),
        dict(title='Check water heater', category='Maintenance', assigned_to=alex.id, frequency='monthly',
             due_date=today + timedelta(days=15), estimated_effort=1, priority='low', status='pending'),
    ]

    for d in chores_data:
        c = Chore(**d)
        db.session.add(c)
    db.session.flush()

    history_entries = [
        ('Wash dishes', alex.id, 8, 2, 'Kitchen'),
        ('Vacuum living room', jordan.id, 8, 2, 'Cleaning'),
        ('Do laundry', alex.id, 8, 2, 'Laundry'),
        ('Take out trash', jordan.id, 8, 1, 'Outdoor'),
        ('Wash dishes', jordan.id, 7, 2, 'Kitchen'),
        ('Clean bathrooms', alex.id, 7, 3, 'Cleaning'),
        ('Do laundry', jordan.id, 7, 2, 'Laundry'),
        ('Take out trash', alex.id, 7, 1, 'Outdoor'),
        ('Grocery shopping', jordan.id, 7, 3, 'Errands'),
        ('Wash dishes', alex.id, 6, 2, 'Kitchen'),
        ('Vacuum living room', jordan.id, 6, 2, 'Cleaning'),
        ('Do laundry', alex.id, 6, 2, 'Laundry'),
        ('Wipe down counters', jordan.id, 6, 1, 'Kitchen'),
        ('Change bed sheets', alex.id, 6, 3, 'Laundry'),
        ('Mow lawn', jordan.id, 6, 4, 'Outdoor'),
        ('Clean bathrooms', alex.id, 5, 3, 'Cleaning'),
        ('Do laundry', jordan.id, 5, 2, 'Laundry'),
        ('Take out trash', jordan.id, 5, 1, 'Outdoor'),
        ('Clean stovetop', alex.id, 5, 2, 'Kitchen'),
        ('Replace HVAC filter', alex.id, 5, 2, 'Maintenance'),
        ('Wash dishes', jordan.id, 4, 2, 'Kitchen'),
        ('Vacuum bedrooms', alex.id, 4, 2, 'Cleaning'),
        ('Grocery shopping', jordan.id, 4, 3, 'Errands'),
        ('Fold and put away clothes', alex.id, 4, 2, 'Laundry'),
        ('Water plants', jordan.id, 4, 1, 'Outdoor'),
        ('Water plants', jordan.id, 4, 1, 'Outdoor'),
        ('Wash dishes', alex.id, 3, 2, 'Kitchen'),
        ('Clean bathrooms', jordan.id, 3, 3, 'Cleaning'),
        ('Do laundry', alex.id, 3, 2, 'Laundry'),
        ('Mow lawn', jordan.id, 3, 4, 'Outdoor'),
        ('Dust surfaces', alex.id, 3, 2, 'Cleaning'),
        ('Scrub shower tiles', jordan.id, 3, 3, 'Cleaning'),
        ('Wipe down counters', alex.id, 2, 1, 'Kitchen'),
        ('Vacuum living room', jordan.id, 2, 2, 'Cleaning'),
        ('Change bed sheets', alex.id, 2, 3, 'Laundry'),
        ('Take out trash', jordan.id, 2, 1, 'Outdoor'),
        ('Grocery shopping', jordan.id, 2, 3, 'Errands'),
        ('Sweep porch', alex.id, 2, 2, 'Outdoor'),
        ('Wash dishes', alex.id, 1, 2, 'Kitchen'),
        ('Clean bathrooms', jordan.id, 1, 3, 'Cleaning'),
        ('Do laundry', alex.id, 1, 2, 'Laundry'),
        ('Water plants', jordan.id, 1, 1, 'Outdoor'),
        ('Wash towels', jordan.id, 1, 2, 'Laundry'),
        ('Replace HVAC filter', alex.id, 1, 2, 'Maintenance'),
    ]

    for title, user_id, weeks_ago, effort, cat in history_entries:
        ts = now() - timedelta(weeks=weeks_ago) + timedelta(days=2)
        h = ChoreHistory(
            chore_title=title,
            completed_by=user_id,
            completed_at=ts,
            effort_points=effort,
            category=cat,
        )
        db.session.add(h)

    db.session.commit()
    print('Seed data inserted.')


# ── Helpers ──────────────────────────────────────────────────────────────────

def next_due_date(frequency, from_date):
    if frequency == 'daily':
        return from_date + timedelta(days=1)
    elif frequency == 'weekly':
        return from_date + timedelta(weeks=1)
    elif frequency == 'biweekly':
        return from_date + timedelta(weeks=2)
    elif frequency == 'monthly':
        return from_date + timedelta(days=30)
    return None


# ── Page Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chores')
def chores_page():
    return render_template('chores.html')

@app.route('/calendar')
def calendar_page():
    return render_template('calendar.html')

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')


# ── API Routes ───────────────────────────────────────────────────────────────

@app.route('/api/users')
def api_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@app.route('/api/dashboard')
def api_dashboard():
    today = date.today()
    week_end = today + timedelta(days=7)
    week_start = today - timedelta(days=today.weekday())

    todays = Chore.query.filter(
        Chore.due_date == today,
        Chore.status != 'completed'
    ).all()

    overdue = Chore.query.filter(
        Chore.due_date < today,
        Chore.status != 'completed'
    ).all()

    upcoming = Chore.query.filter(
        Chore.due_date > today,
        Chore.due_date <= week_end,
        Chore.status != 'completed'
    ).all()

    users = User.query.all()
    fairness = []
    for u in users:
        hist = ChoreHistory.query.filter(
            ChoreHistory.completed_by == u.id,
            ChoreHistory.completed_at >= datetime.combine(week_start, datetime.min.time())
        ).all()
        completed_week = len(hist)
        effort_week = sum(h.effort_points for h in hist)
        pending_count = Chore.query.filter(
            Chore.assigned_to == u.id,
            Chore.status != 'completed'
        ).count()
        fairness.append({
            'user': u.to_dict(),
            'completed_week': completed_week,
            'effort_week': effort_week,
            'pending_count': pending_count,
        })

    return jsonify({
        'today': [c.to_dict() for c in todays],
        'overdue': [c.to_dict() for c in overdue],
        'upcoming': [c.to_dict() for c in upcoming],
        'fairness': fairness,
    })


@app.route('/api/chores', methods=['GET'])
def api_chores():
    q = Chore.query
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('search', '').strip()

    if user_id:
        q = q.filter(Chore.assigned_to == int(user_id))
    if category:
        q = q.filter(Chore.category == category)
    if status:
        q = q.filter(Chore.status == status)
    if priority:
        q = q.filter(Chore.priority == priority)
    if search:
        q = q.filter(Chore.title.ilike(f'%{search}%'))

    chores = q.order_by(Chore.due_date.asc().nullsfirst(), Chore.priority.desc()).all()
    return jsonify([c.to_dict() for c in chores])


@app.route('/api/chores', methods=['POST'])
def api_create_chore():
    data = request.get_json()
    due = None
    if data.get('due_date'):
        try:
            due = date.fromisoformat(data['due_date'])
        except Exception:
            pass

    chore = Chore(
        title=data.get('title', 'Untitled'),
        description=data.get('description', ''),
        category=data.get('category', 'General'),
        assigned_to=data.get('assigned_to') or None,
        frequency=data.get('frequency', 'once'),
        due_date=due,
        estimated_effort=int(data.get('estimated_effort', 1)),
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'pending'),
        notes=data.get('notes', ''),
    )
    db.session.add(chore)
    db.session.commit()
    return jsonify(chore.to_dict()), 201


@app.route('/api/chores/<int:chore_id>', methods=['PUT'])
def api_update_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    data = request.get_json()

    if 'title' in data:
        chore.title = data['title']
    if 'description' in data:
        chore.description = data['description']
    if 'category' in data:
        chore.category = data['category']
    if 'assigned_to' in data:
        chore.assigned_to = data['assigned_to'] or None
    if 'frequency' in data:
        chore.frequency = data['frequency']
    if 'due_date' in data:
        chore.due_date = date.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'estimated_effort' in data:
        chore.estimated_effort = int(data['estimated_effort'])
    if 'priority' in data:
        chore.priority = data['priority']
    if 'status' in data:
        chore.status = data['status']
    if 'notes' in data:
        chore.notes = data['notes']

    chore.updated_at = now()
    db.session.commit()
    return jsonify(chore.to_dict())


@app.route('/api/chores/<int:chore_id>', methods=['DELETE'])
def api_delete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    db.session.delete(chore)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/chores/<int:chore_id>/complete', methods=['POST'])
def api_complete_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    ts = now()
    chore.status = 'completed'
    chore.completed_at = ts
    chore.updated_at = ts

    history = ChoreHistory(
        original_chore_id=chore.id,
        chore_title=chore.title,
        completed_by=chore.assigned_to,
        completed_at=ts,
        effort_points=chore.estimated_effort,
        category=chore.category,
    )
    db.session.add(history)

    if chore.frequency not in ('once', None):
        base = chore.due_date or date.today()
        new_due = next_due_date(chore.frequency, base)
        if new_due:
            next_chore = Chore(
                title=chore.title,
                description=chore.description,
                category=chore.category,
                assigned_to=chore.assigned_to,
                frequency=chore.frequency,
                due_date=new_due,
                estimated_effort=chore.estimated_effort,
                priority=chore.priority,
                status='pending',
                notes=chore.notes,
                parent_chore_id=chore.id,
            )
            db.session.add(next_chore)

    db.session.commit()
    return jsonify({'success': True, 'history': history.to_dict()})


@app.route('/api/chores/<int:chore_id>/swap', methods=['POST'])
def api_swap_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    users = User.query.all()
    user_ids = [u.id for u in users]
    if chore.assigned_to in user_ids:
        other = [uid for uid in user_ids if uid != chore.assigned_to]
        chore.assigned_to = other[0] if other else chore.assigned_to
    else:
        chore.assigned_to = user_ids[0] if user_ids else None
    chore.updated_at = now()
    db.session.commit()
    return jsonify(chore.to_dict())


@app.route('/api/chores/<int:chore_id>/snooze', methods=['POST'])
def api_snooze_chore(chore_id):
    chore = Chore.query.get_or_404(chore_id)
    data = request.get_json() or {}
    days = int(data.get('days', 1))
    base = chore.due_date or date.today()
    chore.due_date = base + timedelta(days=days)
    chore.updated_at = now()
    db.session.commit()
    return jsonify(chore.to_dict())


@app.route('/api/calendar-chores')
def api_calendar_chores():
    chores = Chore.query.filter(
        Chore.due_date.isnot(None),
        Chore.status != 'completed'
    ).all()
    events = []
    for c in chores:
        events.append({
            'id': c.id,
            'title': c.title,
            'date': c.due_date.isoformat(),
            'category': c.category,
            'priority': c.priority,
            'assigned_to': c.assigned_to,
            'assigned_user': c.user.to_dict() if c.user else None,
            'status': c.status,
            'estimated_effort': c.estimated_effort,
        })
    return jsonify(events)


@app.route('/api/analytics')
def api_analytics():
    period = request.args.get('period', 'week')
    today = now()

    if period == 'week':
        start = today - timedelta(days=today.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    users = User.query.all()
    user_stats = []
    for u in users:
        hist = ChoreHistory.query.filter(
            ChoreHistory.completed_by == u.id,
            ChoreHistory.completed_at >= start
        ).all()
        user_stats.append({
            'user': u.to_dict(),
            'completed': len(hist),
            'effort': sum(h.effort_points for h in hist),
        })

    all_hist = ChoreHistory.query.filter(ChoreHistory.completed_at >= start).all()
    cat_map = {}
    for h in all_hist:
        cat = h.category or 'General'
        cat_map[cat] = cat_map.get(cat, 0) + h.effort_points
    category_breakdown = [{'category': k, 'effort': v} for k, v in sorted(cat_map.items(), key=lambda x: -x[1])]

    weekly_trends = []
    for week_offset in range(7, -1, -1):
        wk_start = today - timedelta(weeks=week_offset)
        wk_start = wk_start - timedelta(days=wk_start.weekday())
        wk_start = wk_start.replace(hour=0, minute=0, second=0, microsecond=0)
        wk_end = wk_start + timedelta(days=7)
        label = wk_start.strftime('%b %d')
        per_user = {}
        for u in users:
            count = ChoreHistory.query.filter(
                ChoreHistory.completed_by == u.id,
                ChoreHistory.completed_at >= wk_start,
                ChoreHistory.completed_at < wk_end
            ).count()
            per_user[u.name] = count
        weekly_trends.append({'week': label, 'data': per_user})

    overdue_chores = Chore.query.filter(
        Chore.due_date < date.today(),
        Chore.status != 'completed'
    ).order_by(Chore.due_date.asc()).all()

    total_completed = ChoreHistory.query.filter(ChoreHistory.completed_at >= start).count()
    total_effort = db.session.query(db.func.sum(ChoreHistory.effort_points)).filter(
        ChoreHistory.completed_at >= start
    ).scalar() or 0

    return jsonify({
        'user_stats': user_stats,
        'category_breakdown': category_breakdown,
        'weekly_trends': weekly_trends,
        'total_completed': total_completed,
        'total_effort': total_effort,
        'overdue_count': len(overdue_chores),
        'overdue_chores': [c.to_dict() for c in overdue_chores[:5]],
    })


@app.route('/api/suggest-assignee')
def api_suggest_assignee():
    today = now()
    week_start = today - timedelta(days=today.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    users = User.query.all()
    min_effort = None
    suggested = None
    for u in users:
        effort = db.session.query(db.func.sum(ChoreHistory.effort_points)).filter(
            ChoreHistory.completed_by == u.id,
            ChoreHistory.completed_at >= week_start
        ).scalar() or 0
        if min_effort is None or effort < min_effort:
            min_effort = effort
            suggested = u

    return jsonify({'user_id': suggested.id if suggested else None,
                    'user': suggested.to_dict() if suggested else None})


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, port=5000)
