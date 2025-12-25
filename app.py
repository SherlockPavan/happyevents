from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TimeField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret_key_for_forms"

# --- Database ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Email ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
mail = Mail(app)

# --- Database Model ---
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)

# --- Booking Form ---
class BookingForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone Number", validators=[DataRequired()])
    event_type = SelectField("Event Type", choices=[
        ("wedding", "Wedding"),
        ("birthday", "Birthday Party"),
        ("corporate", "Corporate Event"),
        ("other", "Other")
    ], validators=[DataRequired()])
    date = DateField("Event Date", validators=[DataRequired()])
    time = TimeField("Event Time", validators=[DataRequired()])
    submit = SubmitField("Book Event")

# --- Admin Login Form ---
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# --- Admin Required Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Please login as admin to access this page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/booking", methods=["GET", "POST"])
def booking():
    form = BookingForm()
    if form.validate_on_submit():
        new_booking = Booking(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            event_type=form.event_type.data,
            date=str(form.date.data),
            time=str(form.time.data)
        )
        db.session.add(new_booking)
        db.session.commit()

        # Email confirmation
        msg = Message(
            "Event Booking Confirmation",
            sender="your_email@gmail.com",
            recipients=[form.email.data]
        )
        msg.body = f"Hello {form.name.data},\n\nYour {form.event_type.data} is booked for {form.date.data} at {form.time.data}.\n\nThank you!"
        mail.send(msg)

        flash(f"Thank you {form.name.data}! Your event has been booked.")
        return redirect(url_for("booking"))

    return render_template("booking.html", form=form)

# --- Admin Login ---
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Hardcoded admin credentials (replace with database later)
        if form.username.data == "admin" and form.password.data == "password123":
            session["admin_logged_in"] = True
            flash("Logged in successfully!")
            return redirect(url_for("admin"))
        else:
            flash("Invalid credentials!")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully.")
    return redirect(url_for("home"))

# --- Admin Dashboard ---
@app.route("/admin")
@admin_required
def admin():
    bookings = Booking.query.order_by(Booking.date).all()
    return render_template("admin.html", bookings=bookings)


# --- API for FullCalendar ---
@app.route("/api/bookings")
@admin_required
def api_bookings():
    bookings = Booking.query.all()
    events = []
    colors = {"wedding":"#ff7f50","birthday":"#1e90ff","corporate":"#32cd32","other":"#ffa500"}
    for b in bookings:
        events.append({
            "id": b.id,
            "title": f"{b.event_type.capitalize()} - {b.name}",
            "start": f"{b.date}T{b.time}",
            "color": colors.get(b.event_type, "#808080")
        })
    return jsonify(events)

# --- Delete Booking ---
@app.route("/delete/<int:id>")
@admin_required
def delete_booking(id):
    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted successfully!")
    return redirect(url_for("admin"))

# Create the database tables
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

