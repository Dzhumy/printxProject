import json
import os
import csv
import shutil

from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from markupsafe import Markup
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
# Forms
from webforms import LoginForm, CreateMachine, CreateOrder, UploadForm, SolutionForm
# Database
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# Create a Flask Instance
app = Flask(__name__)
# Secret Key
app.config['SECRET_KEY'] = "printx-secretkey"
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Files
app.config['UPLOAD_FOLDER'] = 'static/files'
ALLOWED_EXTENSIONS = {'csv'}

# Flask Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "alert-warning"


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/about')
@login_required
def about():
    return render_template("about.html")


@app.route('/create-machine', methods=['GET', 'POST'])
@login_required
def create_machine():
    form = CreateMachine()
    if form.validate_on_submit():
        machine = Machine(name=form.name.data, equipment_capacity=form.equipment_capacity.data, available_hours=form.available_hours.data)
        db.session.add(machine)
        db.session.commit()
        flash(Markup("<b>Machine:</b> " + str(form.name.data) + " ; <b>Capacity Of Equipment:</b> " + str(form.equipment_capacity.data) + " ; <b>Available Hours:</b> " + str(form.available_hours.data) + " - has been added successfully!"))
        form.name.data = ''
        form.equipment_capacity.data = ''
        form.available_hours.data = ''
        return redirect(request.url)
    return render_template("create-machine.html", form=form)


@app.route('/create-order', methods=['GET', 'POST'])
@login_required
def create_order():
    form = CreateOrder()
    if form.validate_on_submit():
        order = Order(name=form.name.data, order_type=form.order_type.data, count=form.count.data)
        db.session.add(order)
        db.session.commit()
        flash(Markup("<b>Item:</b> " + form.name.data + " ; <b>Type:</b> " + form.order_type.data + " ; <b>Count:</b> " + str(form.count.data) + " - has been added successfully!"))
        form.name.data = ''
        form.order_type.data = ''
        form.count.data = ''
        return redirect(request.url)
    return render_template("create-order.html", form=form)


@app.route('/create-solution', methods=['GET', 'POST'])
@login_required
def create_solution():
    form = SolutionForm()
    if request.method == 'POST' and form.validate_on_submit():
        order_list = json.loads(request.form['order_list'].replace("'", '"'))
        machine_list = json.loads(request.form['machine_list'].replace("'", '"'))
        folder_name = request.form['folder_name']
        time_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        directory = app.config['UPLOAD_FOLDER'] + "/Solutions/" + time_now + "_" + folder_name
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, "order_list.json"), "w", encoding='utf8') as f:
            json.dump(order_list, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        with open(os.path.join(directory, "machine_list.json"), "w", encoding='utf8') as f:
            json.dump(machine_list, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        return redirect(url_for('view_solutions'))

    if form.folder_name.errors:
        flash(form.folder_name.errors[0])

    is_result, order_list, machine_list = optimization_algorithm()
    if is_result:
        return render_template("create-solution.html", is_result=is_result, order_list=order_list, machine_list=machine_list, form=form)
    else:
        return render_template("create-solution.html", is_result=is_result)


@app.route('/delete-machine/<int:id>')
@login_required
def delete_machine(id):
    machine_to_delete = Machine.query.get_or_404(id)
    try:
        db.session.delete(machine_to_delete)
        db.session.commit()
        flash("Machine Deleted Successfully!")
        return render_template("view-machines.html", values=Machine.query.all())
    except:
        flash("Error While Deleting User!")
        return render_template("view-machines.html", values=Machine.query.all())


@app.route('/delete-order/<int:id>')
@login_required
def delete_order(id):
    order_to_delete = Order.query.get_or_404(id)
    try:
        db.session.delete(order_to_delete)
        db.session.commit()
        flash("Order Deleted Successfully!")
        return render_template("view-orders.html", values=Order.query.all())
    except:
        flash("Error While Deleting Machine!")
        return render_template("view-orders.html", values=Order.query.all())



@app.route('/delete-solution/<string:directory>')
@login_required
def delete_solution(directory):
    folder_path = app.config['UPLOAD_FOLDER'] + '/Solutions/' + directory
    shutil.rmtree(folder_path)
    directory = app.config['UPLOAD_FOLDER'] + "/Solutions"
    directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    flash("Solution Deleted Successfully!")
    return render_template("view-solutions.html", directories=directories)


@app.route('/')
@app.route('/home')
@login_required
def index():
    return render_template("index.html")


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


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


@app.route('/update-machine/<int:id>', methods=['GET', 'POST'])
@login_required
def update_machine(id):
    form = CreateMachine()
    machine_to_update = Machine.query.get_or_404(id)
    if form.validate_on_submit():
        machine_to_update.name = request.form['name']
        machine_to_update.equipment_capacity = request.form['equipment_capacity']
        machine_to_update.available_hours = request.form['available_hours']
        try:
            db.session.commit()
            flash("Machine Updated Successfully!")
            return redirect(url_for('view_machines'))
        except:
            flash("Error!")
            return render_template("update-machine.html", form=form, machine_to_update=machine_to_update)
    else:
        return render_template("update-machine.html", form=form, machine_to_update=machine_to_update, id=id)


# Update Database Record
@app.route('/update-order/<int:id>', methods=['GET', 'POST'])
@login_required
def update_order(id):
    form = CreateOrder()
    order_to_update = Order.query.get_or_404(id)
    if form.validate_on_submit():
        order_to_update.name = request.form['name']
        order_to_update.order_type = request.form['order_type']
        order_to_update.count = request.form['count']
        try:
            db.session.commit()
            flash("Order Updated Successfully!")
            return redirect(url_for('view_orders'))
        except:
            flash("Error!")
            return render_template("update-order.html", form=form, order_to_update=order_to_update)
    else:
        return render_template("update-order.html", form=form, order_to_update=order_to_update, id=id)


def save_file(form, folder):
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    uploaded_file = form.file.data
    file_name = date + "_" + form.file_name.data.lower().replace(" ", "_") + ".csv"
    filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'] + folder, secure_filename(file_name))
    uploaded_file.save(filepath)

    return filepath


@app.route('/solution/<string:directory>', methods=['GET', 'POST'])
@login_required
def solution(directory):
    folder = app.config['UPLOAD_FOLDER'] + "/Solutions/" + directory
    order_list_json = os.path.join(folder, 'order_list.json')
    machine_list_json = os.path.join(folder, 'machine_list.json')
    with open(order_list_json, 'r', encoding='utf-8') as f:
        order_list = json.load(f)
    with open(machine_list_json, 'r', encoding='utf-8') as f:
        machine_list = json.load(f)
    return render_template("solution.html", order_list=order_list, machine_list=machine_list)



@app.route('/upload-machine', methods=['GET', 'POST'])
@login_required
def upload_machine():
    form = UploadForm()
    if form.validate_on_submit():
        folder = '/Machines'
        filepath = save_file(form, folder)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                # Process CSV file
                reader = csv.reader(file, delimiter=',')
                next(reader)
                for row in reader:
                    name, equipment_capacity, available_hours = row
                    machine = Machine(name=name, equipment_capacity=equipment_capacity, available_hours=available_hours)
                    db.session.add(machine)
                db.session.commit()
                flash('File successfully uploaded!')
        except:
            flash("Error in file processing!")
            return redirect(url_for('upload_machine'))
        form.file_name.data = ''
        form.file.data = None
        return redirect(url_for('view_machines'))

    if form.file_name.errors:
        flash(form.file_name.errors[0])

    if form.file.errors:
        flash(form.file.errors[0])

    return render_template("upload-machine.html", form=form)


@app.route('/upload-order', methods=['GET', 'POST'])
@login_required
def upload_order():
    form = UploadForm()
    if form.validate_on_submit():
        folder = '/Orders'
        filepath = save_file(form, folder)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                # Process CSV file
                reader = csv.reader(file, delimiter=',')
                next(reader)
                for row in reader:
                    name, order_type, count = row
                    order = Order(name=name, order_type=order_type, count=count)
                    db.session.add(order)
                db.session.commit()
                flash('File successfully uploaded!')
        except:
            flash("Error in file processing!")
            return redirect(url_for('upload_order'))
        form.file_name.data = ''
        form.file.data = None
        return redirect(url_for('view_orders'))

    if form.file_name.errors:
        flash(form.file_name.errors[0])

    if form.file.errors:
        flash(form.file.errors[0])

    return render_template("upload-order.html", form=form)


@app.route('/view-machines')
@login_required
def view_machines():
    return render_template("view-machines.html", values=Machine.query.all())


@app.route('/view-orders')
@login_required
def view_orders():
    return render_template("view-orders.html", values=Order.query.all())


@app.route('/view-solutions')
@login_required
def view_solutions():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    directory = os.path.join(base_dir, app.config['UPLOAD_FOLDER'], 'Solutions')
    directories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return render_template("view-solutions.html", directories=directories)


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


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order_type = db.Column(db.String(100))
    count = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, order_type, count):
        self.name = name
        self.order_type = order_type
        self.count = count


class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    equipment_capacity = db.Column(db.Integer, nullable=False)
    available_hours = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, equipment_capacity, available_hours):
        self.name = name
        self.equipment_capacity = equipment_capacity
        self.available_hours = available_hours


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


# Optmization model
from optimization_model import optimization_algorithm


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
