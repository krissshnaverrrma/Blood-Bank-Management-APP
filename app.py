import os
import qrcode
import io
import csv
from flask import make_response
from flask import jsonify
import uuid
from flask import send_file
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_migrate import Migrate
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
DB_URL = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.secret_key = os.getenv("SECRET_KEY", "fallback_default_key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
os.makedirs(os.path.join(app.root_path,
            app.config['UPLOAD_FOLDER']), exist_ok=True)
db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()
    print("✅ Database tables confirmed/created successfully.")

s = URLSafeTimedSerializer(app.secret_key)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    blood_group = db.Column(db.String(5), nullable=True)
    profile_image = db.Column(
        db.String(150), nullable=False, default='default.svg')


class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True)


class BloodStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_group = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, default=0)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    hospital_name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, default=0.0)
    date = db.Column(db.DateTime, default=datetime.now)
    payment_status = db.Column(db.String(20), default='Pending')
    utr_number = db.Column(db.String(50), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def send_email_notification(to_email, email_subject, template_name, **context):
    try:
        html_body = render_template(template_name, **context)
        msg = Message(
            email_subject, sender=app.config['MAIL_USERNAME'], recipients=[to_email])
        msg.html = html_body
        mail.send(msg)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message_body = request.form['message']
        send_email_notification(
            email,
            f"We received your message: {subject}",
            "email/contact_confirmation.html",
            name=name,
            subject=subject
        )
        flash("Message sent successfully! Check your email for confirmation.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        blood_group = request.form['blood_group']
        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(
            full_name=fullname,
            username=username,
            email=email,
            password_hash=hashed_pw,
            blood_group=blood_group
        )
        db.session.add(new_user)
        db.session.commit()
        send_email_notification(email, "Welcome to Blood-Management-APP! 🩸",
                                "email/welcome_message.html", username=username)
        flash("Account created! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('landing'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('landing'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(user.email, salt='email-recover')
            link = url_for('reset_password', token=token, _external=True)
            send_email_notification(
                email, "Reset Your Password", "email/forgot_password.html", link=link)
            flash("Check your email for the reset link.", "info")
            return redirect(url_for('login'))
        else:
            flash("Email not found.", "danger")
    return render_template('auth/forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-recover', max_age=3600)
    except:
        flash("Link expired or invalid.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        user.password_hash = generate_password_hash(
            request.form['password'], method='scrypt')
        db.session.commit()
        send_email_notification(
            email, "Password Updated Successfully", "email/recover_password.html")
        flash("Password updated! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('auth/reset_password.html')


@app.route('/dashboard')
@login_required
def dashboard():
    stock = BloodStock.query.all()
    donors = Donor.query.all()
    transactions = Transaction.query.order_by(
        Transaction.date.desc()).limit(5).all()
    return render_template('dashboard.html', stock=stock, donors=donors, transactions=transactions)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.bio = request.form['bio']
        new_email = request.form['email']
        if new_email != current_user.email:
            if User.query.filter_by(email=new_email).first():
                flash("That email is already in use.", "danger")
                return redirect(url_for('edit_profile'))
            current_user.email = new_email
        if request.form.get('remove_photo') == 'true':
            current_user.profile_image = 'default.svg'
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"user_{current_user.id}_{filename}"
                file.save(os.path.join(app.root_path,
                          app.config['UPLOAD_FOLDER'], unique_filename))
                current_user.profile_image = unique_filename
        db.session.commit()
        flash("Profile Updated Successfully!", "success")
        return redirect(url_for('profile'))
    return render_template('edit_profile.html')


@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        email_addr = current_user.email
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        send_email_notification(
            email_addr, "Account Deleted", "email/delete_account.html")
        flash("Your account has been deleted.", "warning")
        return redirect(url_for('landing'))
    return render_template('auth/delete_account.html')


@app.route('/add_donor', methods=['GET', 'POST'])
@login_required
def add_donor():
    if request.method == 'POST':
        name = request.form['name']
        b_group = request.form['blood_group']
        phone = request.form['phone']
        db.session.add(Donor(name=name, blood_group=b_group, phone=phone))
        if not BloodStock.query.filter_by(blood_group=b_group).first():
            db.session.add(BloodStock(blood_group=b_group, units=0))
        db.session.commit()
        flash("Donor Added!", "success")
        return redirect(url_for('dashboard'))
    return render_template('add_donor.html')


@app.route('/donate/<int:id>')
@login_required
def donate_blood(id):
    donor = Donor.query.get(id)
    stock = BloodStock.query.filter_by(blood_group=donor.blood_group).first()
    if stock:
        stock.units += 1
        donor.last_donation_date = datetime.now().date()
        db.session.commit()
        flash(f"Thank you {donor.name}! Stock updated.", "success")
    return redirect(url_for('dashboard'))


@app.route('/delete_donor/<int:id>')
@login_required
def delete_donor(id):
    db.session.delete(Donor.query.get(id))
    db.session.commit()
    flash("Donor deleted.", "info")
    return redirect(url_for('dashboard'))


@app.route('/issue_blood', methods=['GET', 'POST'])
@login_required
def issue_blood():
    if request.method == 'GET':
        return render_template('issue_blood.html')
    if request.method == 'POST':
        try:
            data = request.get_json()
            patient = data.get('patient')
            hospital = data.get('hospital')
            b_group = data.get('blood_group')
            units = int(data.get('units'))
            utr = data.get('utr')
            price_per_unit = 500.0
            total = units * price_per_unit
            stock = BloodStock.query.filter_by(blood_group=b_group).first()
            if not stock or stock.units < units:
                return jsonify({"status": "error", "message": f"Insufficient stock for {b_group}! Only {stock.units if stock else 0} available."}), 400
            stock.units -= units
            new_trans = Transaction(
                patient_name=patient,
                hospital_name=hospital,
                blood_group=b_group,
                units=units,
                total_amount=total,
                payment_status="Paid",
                utr_number=utr,
                date=datetime.now()
            )
            db.session.add(new_trans)
            db.session.commit()
            return jsonify({
                "status": "success",
                "redirect": url_for('transactions'),
                "message": "Blood Issued Successfully"
            })
        except Exception as e:
            print(f"ISSUE BLOOD ERROR: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/transaction_details/<int:id>')
@login_required
def transaction_details(id):
    transaction = Transaction.query.get_or_404(id)
    return render_template('issue_blood_transaction.html', t=transaction)


@app.route('/invoice/<int:id>')
@login_required
def view_invoice(id):
    return render_template('invoice.html', t=Transaction.query.get_or_404(id))


@app.route('/support_us')
@login_required
def support_us():
    return render_template('donate_money.html')


@app.route('/generate_qr')
@login_required
def generate_qr():
    amount = request.args.get('amount')
    my_upi_id = os.getenv("UPI_ID", "default@upi")
    my_name = "Krishna Verma"
    upi_url = f"upi://pay?pa={my_upi_id}&pn={my_name}&am={amount}&cu=INR"
    img = qrcode.make(upi_url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@app.route('/transactions')
@login_required
def transactions():
    all_trans = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=all_trans)


@app.route('/export_transactions_csv')
@login_required
def export_transactions_csv():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Invoice ID', 'Patient Name', 'Hospital Name', 'Blood Group',
        'Units', 'Total Amount (INR)', 'Payment Status', 'UTR Number', 'Date'
    ])
    for t in transactions:
        writer.writerow([
            t.id,
            t.patient_name,
            t.hospital_name,
            t.blood_group,
            t.units,
            t.total_amount,
            t.payment_status,
            t.utr_number,
            t.date.strftime('%Y-%m-%d %H:%M:%S')
        ])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=transactions_export.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route('/confirm_donation', methods=['POST'])
@login_required
def confirm_donation():
    try:
        data = request.get_json()
        amount = data.get('amount', '0')
        user_utr = data.get('utr', 'N/A')
        donor_name = data.get(
            'name') or current_user.full_name or current_user.username
        donor_email = data.get('email') or current_user.email
        date_now = datetime.now().strftime("%d %b, %Y %I:%M %p")
        send_email_notification(
            donor_email,
            "Donation Received - Verification Completed",
            "email/donation_receipt.html",
            name=donor_name,
            amount=amount,
            trans_id=user_utr,
            date=date_now
        )
        return jsonify({"status": "success", "message": "Receipt sent!"})
    except Exception as e:
        print(f"PAYMENT ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
