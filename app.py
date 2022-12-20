import datetime
import os
from flask import Flask, render_template, url_for, request, redirect, session, flash
from datetime import datetime,timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Create a Flask Instance
app = Flask(__name__)
# Secret Key
app.config['SECRET_KEY'] = "printx-secretkey"
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = 'static/files'

# Flask Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "alert-warning"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, count):
        self.name = name
        self.count = count


class CreateDelivery(FlaskForm):
    name = StringField("Enter Name:", validators=[DataRequired()])
    count = IntegerField("Enter number of items:", validators=[DataRequired(), NumberRange(min=1, message='Must enter a number greater than 0')])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    user_name = StringField("Username", validators=[DataRequired()], render_kw={"placeholder": "Enter Username"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Enter Password"})
    submit = SubmitField("Login")


class UploadForm(FlaskForm):
    file = FileField("Enter deliveries file: ", validators=[DataRequired()])
    submit = SubmitField("Upload")


@app.route('/')
@app.route('/home')
@login_required
def index():
    return render_template("index.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.user_name.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Wrong Username/Password - Try Again!", "alert-warning")
        else:
            flash("Wrong Username/Password - Try Again!", "alert-warning")
    return render_template("login.html", form=form)


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!", "alert-warning")
    return redirect(url_for("login"))


@app.route('/create-delivery', methods=['GET', 'POST'])
@login_required
def create_delivery():
    form = CreateDelivery()
    if form.validate_on_submit():
        delivery = Delivery(name=form.name.data, count=form.count.data)
        db.session.add(delivery)
        db.session.commit()
        flash("Item: " + str(form.name.data) + " ; Count: " + str(form.count.data) + " - has been added successfully!")
        form.name.data = ''
        form.count.data = ''
        return redirect(request.url)
    return render_template("create-delivery.html", form=form)


@app.route('/upload-delivery', methods=['GET', 'POST'])
@login_required
def upload_delivery():
    form = UploadForm()

    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filenane)
        form.file.data.save('uploads/'+filename)
        return redirect(url_for('upload_delivery'))

    return render_template("upload-delivery.html", form=form)


# Update Database Record
@app.route('/update-order/<int:id>', methods=['GET', 'POST'])
@login_required
def update_order(id):
    form = CreateDelivery()
    order_to_update = Delivery.query.get_or_404(id)
    if form.validate_on_submit():
        order_to_update.name = request.form['name']
        order_to_update.count = request.form['count']
        try:
            db.session.commit()
            flash("Item Updated Successfully!")
            return redirect(url_for('view_deliveries'))
        except:
            flash("Error!")
            return render_template("update-order.html", form=form, order_to_update=order_to_update)
    else:
        return render_template("update-order.html", form=form, order_to_update=order_to_update, id=id)


@app.route('/delete/<int:id>')
@login_required
def delete_order(id):
    order_to_delete = Delivery.query.get_or_404(id)
    name = None
    form = CreateDelivery()
    try:
        db.session.delete(order_to_delete)
        db.session.commit()
        flash("Order Deleted Successfully!")
        return render_template("view-deliveries.html", values=Delivery.query.all())
    except:
        flash("Error While Deleting User!")
        return render_template("view-deliveries.html", values=Delivery.query.all())


@app.route('/view_deliveries')
@login_required
def view_deliveries():
    # delete_table_records(Delivery.query.all())
    return render_template("view-deliveries.html", values=Delivery.query.all())


@app.route('/about')
@login_required
def about():
    return render_template("about.html")


# Invalid URL error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


# IN CASE NEEDED - TABLE RECORD DELETE
# def delete_table_records(value):
#     for item in value:
#         db.session.delete(item)
#     db.session.commit()

# IN CASE NEEDED - USER CREATION
# def create_user(username,password):
#     hashed_pw = generate_password_hash(password, "sha256")
#     user_create = Users(username=username, password_hash=hashed_pw)
#     db.session.add(user_create)
#     db.session.commit()


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
