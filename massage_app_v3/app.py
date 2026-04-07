from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production-please')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///massage.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Massage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_sl = db.Column(db.String(120), nullable=False)
    name_de = db.Column(db.String(120), nullable=False)
    name_en = db.Column(db.String(120), nullable=False)
    desc_sl = db.Column(db.String(300))
    desc_de = db.Column(db.String(300))
    desc_en = db.Column(db.String(300))
    duration = db.Column(db.Integer, default=60)
    price = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)

class WorkingHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_index = db.Column(db.Integer, nullable=False)
    day_sl = db.Column(db.String(20))
    day_de = db.Column(db.String(20))
    day_en = db.Column(db.String(20))
    open_time = db.Column(db.String(5))
    close_time = db.Column(db.String(5))
    is_open = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40), nullable=False)
    massage_id = db.Column(db.Integer, db.ForeignKey('massage.id'))
    massage = db.relationship('Massage', backref='appointments')
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(5), nullable=False)
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GalleryPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    alt_text = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text)

def allowed_file(f): return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def is_admin(): return session.get('admin_logged_in')

def get_setting(key, default=''):
    s = SiteSettings.query.filter_by(key=key).first()
    return s.value if s else default

def set_setting(key, value):
    s = SiteSettings.query.filter_by(key=key).first()
    if s: s.value = value
    else: db.session.add(SiteSettings(key=key, value=value))
    db.session.commit()

def auto_archive_past():
    today = date.today()
    past = Appointment.query.filter(Appointment.status == 'confirmed', Appointment.date < today).all()
    for a in past: a.status = 'archived'
    if past: db.session.commit()

def seed_database():
    if not Admin.query.first():
        a = Admin(username='admin'); a.set_password('admin123'); db.session.add(a)
    if not Massage.query.first():
        db.session.add_all([
            Massage(name_sl='Sprostitvena masaža', name_de='Entspannungsmassage', name_en='Relaxing Massage',
                    desc_sl='Zmanjšajte stres in dosežite popolno sprostitev.',
                    desc_de='Stress abbauen und totale Entspannung erreichen.',
                    desc_en='Release tension and achieve total relaxation.', duration=60, price=40.0),
            Massage(name_sl='Športna masaža', name_de='Sportmassage', name_en='Sports Massage',
                    desc_sl='Podpira regeneracijo in izboljšuje gibljivost pri športnikih.',
                    desc_de='Unterstützt Regeneration und verbessert Mobilität für Sportler.',
                    desc_en='Supports recovery and improves mobility for athletes.', duration=60, price=50.0),
            Massage(name_sl='Terapevtska masaža', name_de='Therapeutische Massage', name_en='Therapeutic Massage',
                    desc_sl='Lajšanje bolečin in ciljna terapija za boljšo gibljivost.',
                    desc_de='Schmerzlinderung und gezielte Therapie für bessere Beweglichkeit.',
                    desc_en='Pain relief and targeted therapy for improved mobility.', duration=60, price=45.0),
        ])
    if not WorkingHours.query.first():
        for d in [(0,'Ponedeljek','Montag','Monday','16:30','19:00',True),(1,'Torek','Dienstag','Tuesday','16:30','19:00',True),
                  (2,'Sreda','Mittwoch','Wednesday','16:30','19:00',True),(3,'Četrtek','Donnerstag','Thursday','16:30','19:00',True),
                  (4,'Petek','Freitag','Friday',None,None,False),(5,'Sobota','Samstag','Saturday',None,None,False),
                  (6,'Nedelja','Sonntag','Sunday',None,None,False)]:
            db.session.add(WorkingHours(day_index=d[0],day_sl=d[1],day_de=d[2],day_en=d[3],open_time=d[4],close_time=d[5],is_open=d[6]))
    db.session.commit()

# ── Public ──
@app.route('/')
def index():
    now = date.today().isoformat()
    return render_template('index.html',
        massages=Massage.query.filter_by(active=True).all(),
        hours=WorkingHours.query.order_by(WorkingHours.day_index).all(),
        photos=GalleryPhoto.query.order_by(GalleryPhoto.order).all(),
        phone=get_setting('phone', '+386 40 123 456'),
        email=get_setting('email', 'info@massage-indir.com'),
        now=now)

@app.route('/api/working-hours')
def api_working_hours():
    return jsonify([{'day_index':h.day_index,'day_sl':h.day_sl,'day_de':h.day_de,'day_en':h.day_en,
                     'open_time':h.open_time,'close_time':h.close_time,'is_open':h.is_open}
                    for h in WorkingHours.query.order_by(WorkingHours.day_index).all()])

@app.route('/api/available-slots')
def available_slots():
    date_str, massage_id = request.args.get('date'), request.args.get('massage_id')
    if not date_str or not massage_id: return jsonify([])
    try: appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify([])
    wh = WorkingHours.query.filter_by(day_index=appt_date.weekday()).first()
    if not wh or not wh.is_open: return jsonify([])
    massage = Massage.query.get(massage_id)
    if not massage: return jsonify([])
    oh, om = map(int, wh.open_time.split(':'))
    ch, cm = map(int, wh.close_time.split(':'))
    slots, t = [], oh*60+om
    while t + massage.duration <= ch*60+cm:
        slots.append(f"{t//60:02d}:{t%60:02d}"); t += massage.duration
    booked = {a.time_slot for a in Appointment.query.filter_by(date=appt_date).filter(
        Appointment.status.in_(['pending','confirmed'])).all()}
    return jsonify([s for s in slots if s not in booked])

@app.route('/book', methods=['POST'])
def book():
    d = request.get_json()
    name, phone, email = d.get('name','').strip(), d.get('phone','').strip(), d.get('email','').strip()
    massage_id, date_str, time_slot, note = d.get('massage_id'), d.get('date'), d.get('time_slot'), d.get('note','').strip()
    if not all([name, phone, massage_id, date_str, time_slot]):
        return jsonify({'success':False,'error':'Manjkajo obvezna polja'}), 400
    try: appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except: return jsonify({'success':False,'error':'Neveljaven datum'}), 400
    if Appointment.query.filter_by(date=appt_date, time_slot=time_slot).filter(
            Appointment.status.in_(['pending','confirmed'])).first():
        return jsonify({'success':False,'error':'Ta termin ni več prost'}), 409
    db.session.add(Appointment(name=name,phone=phone,email=email,massage_id=massage_id,
                               date=appt_date,time_slot=time_slot,note=note))
    db.session.commit()
    return jsonify({'success':True})

# ── Admin ──
@app.route('/admin')
def admin():
    if not is_admin(): return redirect(url_for('admin_login'))
    auto_archive_past()
    today = date.today()
    today_appts = Appointment.query.filter(Appointment.date==today,
        Appointment.status.in_(['pending','confirmed'])).order_by(Appointment.time_slot).all()
    upcoming = Appointment.query.filter(Appointment.date>today,
        Appointment.status.in_(['pending','confirmed'])).order_by(Appointment.date,Appointment.time_slot).limit(8).all()
    return render_template('admin/dashboard.html',
        today_appts=today_appts, upcoming=upcoming, today=today,
        pending_count=Appointment.query.filter_by(status='pending').count(),
        confirmed_count=Appointment.query.filter(Appointment.status=='confirmed',Appointment.date>=today).count(),
        archived_count=Appointment.query.filter_by(status='archived').count(),
        total_count=Appointment.query.count())

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        a = Admin.query.filter_by(username=request.form.get('username')).first()
        if a and a.check_password(request.form.get('password')):
            session['admin_logged_in'] = True; return redirect(url_for('admin'))
        flash('Napačno uporabniško ime ali geslo', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None); return redirect(url_for('admin_login'))

@app.route('/admin/appointments')
def admin_appointments():
    if not is_admin(): return redirect(url_for('admin_login'))
    auto_archive_past()
    status = request.args.get('status', 'active')
    today = date.today()
    if status == 'active':
        appts = Appointment.query.filter(Appointment.status.in_(['pending','confirmed']),
            Appointment.date>=today).order_by(Appointment.date,Appointment.time_slot).all()
    elif status == 'pending':
        appts = Appointment.query.filter_by(status='pending').order_by(Appointment.date,Appointment.time_slot).all()
    elif status == 'confirmed':
        appts = Appointment.query.filter(Appointment.status=='confirmed',
            Appointment.date>=today).order_by(Appointment.date,Appointment.time_slot).all()
    elif status == 'cancelled':
        appts = Appointment.query.filter_by(status='cancelled').order_by(Appointment.date.desc()).all()
    elif status == 'archived':
        appts = Appointment.query.filter_by(status='archived').order_by(Appointment.date.desc()).all()
    else:
        appts = Appointment.query.order_by(Appointment.date.desc()).all()
    counts = {
        'active': Appointment.query.filter(Appointment.status.in_(['pending','confirmed']),Appointment.date>=today).count(),
        'pending': Appointment.query.filter_by(status='pending').count(),
        'confirmed': Appointment.query.filter(Appointment.status=='confirmed',Appointment.date>=today).count(),
        'cancelled': Appointment.query.filter_by(status='cancelled').count(),
        'archived': Appointment.query.filter_by(status='archived').count(),
    }
    return render_template('admin/appointments.html', appointments=appts, status=status, counts=counts)

@app.route('/admin/appointment/<int:id>/status', methods=['POST'])
def update_appointment_status(id):
    if not is_admin(): return jsonify({'error':'Ni dovoljeno'}), 401
    a = Appointment.query.get_or_404(id)
    s = request.json.get('status')
    if s in ['pending','confirmed','cancelled','archived']:
        a.status = s; db.session.commit(); return jsonify({'success':True})
    return jsonify({'error':'Neveljaven status'}), 400

@app.route('/admin/appointment/<int:id>/delete', methods=['POST'])
def delete_appointment(id):
    if not is_admin(): return redirect(url_for('admin_login'))
    a = Appointment.query.get_or_404(id); db.session.delete(a); db.session.commit()
    flash('Rezervacija izbrisana.', 'success')
    return redirect(url_for('admin_appointments', status=request.args.get('status','active')))

@app.route('/admin/archive/clear', methods=['POST'])
def clear_archive():
    if not is_admin(): return redirect(url_for('admin_login'))
    Appointment.query.filter_by(status='archived').delete(); db.session.commit()
    flash('Arhiv je bil izpraznjen.', 'success')
    return redirect(url_for('admin_appointments', status='archived'))

@app.route('/admin/massages')
def admin_massages():
    if not is_admin(): return redirect(url_for('admin_login'))
    return render_template('admin/massages.html', massages=Massage.query.all())

@app.route('/admin/massages/add', methods=['POST'])
def admin_massage_add():
    if not is_admin(): return redirect(url_for('admin_login'))
    f = request.form
    db.session.add(Massage(name_sl=f['name_sl'],name_de=f.get('name_de',f['name_sl']),
        name_en=f.get('name_en',f['name_sl']),desc_sl=f.get('desc_sl',''),
        desc_de=f.get('desc_de',''),desc_en=f.get('desc_en',''),
        duration=int(f.get('duration',60)),price=float(f['price'])))
    db.session.commit(); flash('Masaža dodana!','success')
    return redirect(url_for('admin_massages'))

@app.route('/admin/massages/<int:id>/edit', methods=['POST'])
def admin_massage_edit(id):
    if not is_admin(): return redirect(url_for('admin_login'))
    m, f = Massage.query.get_or_404(id), request.form
    m.name_sl=f['name_sl']; m.name_de=f.get('name_de',m.name_sl); m.name_en=f.get('name_en',m.name_sl)
    m.desc_sl=f.get('desc_sl',''); m.desc_de=f.get('desc_de',''); m.desc_en=f.get('desc_en','')
    m.duration=int(f.get('duration',60)); m.price=float(f['price']); m.active='active' in f
    db.session.commit(); flash('Masaža posodobljena!','success')
    return redirect(url_for('admin_massages'))

@app.route('/admin/massages/<int:id>/delete', methods=['POST'])
def admin_massage_delete(id):
    if not is_admin(): return redirect(url_for('admin_login'))
    m = Massage.query.get_or_404(id); db.session.delete(m); db.session.commit()
    flash('Masaža izbrisana.','success'); return redirect(url_for('admin_massages'))

@app.route('/admin/hours', methods=['GET','POST'])
def admin_hours():
    if not is_admin(): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        for h in WorkingHours.query.order_by(WorkingHours.day_index).all():
            h.is_open = f'open_{h.day_index}' in request.form
            h.open_time = request.form.get(f'open_time_{h.day_index}','').strip() or None if h.is_open else None
            h.close_time = request.form.get(f'close_time_{h.day_index}','').strip() or None if h.is_open else None
        db.session.commit(); flash('Delovni čas posodobljen!','success')
        return redirect(url_for('admin_hours'))
    return render_template('admin/hours.html', hours=WorkingHours.query.order_by(WorkingHours.day_index).all())

@app.route('/admin/gallery')
def admin_gallery():
    if not is_admin(): return redirect(url_for('admin_login'))
    return render_template('admin/gallery.html', photos=GalleryPhoto.query.order_by(GalleryPhoto.order).all())

@app.route('/admin/gallery/upload', methods=['POST'])
def admin_gallery_upload():
    if not is_admin(): return redirect(url_for('admin_login'))
    if 'photo' not in request.files:
        flash('Nobena datoteka ni bila izbrana','error'); return redirect(url_for('admin_gallery'))
    file = request.files['photo']
    if file and allowed_file(file.filename):
        base, ext = os.path.splitext(secure_filename(file.filename))
        filename = f"{base}_{int(datetime.utcnow().timestamp())}{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.session.add(GalleryPhoto(filename=filename,alt_text=request.form.get('alt_text',''),order=GalleryPhoto.query.count()))
        db.session.commit(); flash('Fotografija naložena!','success')
    else: flash('Neveljavna vrsta datoteke','error')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/gallery/<int:id>/delete', methods=['POST'])
def admin_gallery_delete(id):
    if not is_admin(): return redirect(url_for('admin_login'))
    p = GalleryPhoto.query.get_or_404(id)
    try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], p.filename))
    except: pass
    db.session.delete(p); db.session.commit(); flash('Fotografija izbrisana.','success')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/settings', methods=['GET','POST'])
def admin_settings():
    if not is_admin(): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        set_setting('phone', request.form.get('phone',''))
        set_setting('email', request.form.get('email',''))
        pw = request.form.get('new_password','').strip()
        if pw: a = Admin.query.first(); a.set_password(pw); db.session.commit()
        flash('Nastavitve shranjene!','success'); return redirect(url_for('admin_settings'))
    return render_template('admin/settings.html',
        phone=get_setting('phone','+386 40 123 456'), email=get_setting('email','info@massage-indir.com'))

from flask import send_from_directory
@app.route('/uploads/<filename>')
def uploaded_file(filename): return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all(); seed_database()
    app.run(debug=True)
