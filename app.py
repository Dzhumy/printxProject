import os
from flask import Flask, render_template, url_for, request, redirect, session, flash
from werkzeug.utils import secure_filename
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt'}

app = Flask(__name__)
app.secret_key = "printx-secretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deliveries.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.permanent_session_lifetime = timedelta(minutes=3)
db = SQLAlchemy(app)


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    def __init__(self, title, count):
        self.title = title
        self.count = count


@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = request.form['nm']
        session["user"] = user
        flash("Login Successful!")
        return redirect(url_for("user"))
    else:
        if "user" in session:
            flash("Already logged in!")
            return redirect(url_for("user"))

        return render_template("login.html")


@app.route("/logout")
def logout():
    flash("You have been logged out!")
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/user")
def user():
    if "user" in session:
        user = session["user"]
        return render_template("user.html", user=user)
    else:
        flash("You are not logged in!")
        return redirect(url_for("login"))


@app.route('/create-delivery', methods=['GET', 'POST'])
def create_delivery():
    if request.method == "POST":
        title = request.form['title']
        count = request.form['count']

        delivery = Delivery(title=title, count=count)

        try:
            db.session.add(delivery)
            db.session.commit()
            return redirect(request.url)
        except:
            return "Input error"
    else:
        return render_template("create-delivery.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload-delivery', methods=['GET', 'POST'])
def upload_delivery():
    if request.method == "POST":
        # Checks if POST request contains the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['filename']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('download_file', name=filename))

    return render_template("upload-delivery.html")

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/view_deliveries')
def view_deliveries():
    # delete_table_records(Delivery.query.all())
    return render_template("view-deliveries.html", values=Delivery.query.all())


# Invalid URL error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


# IN CASE NEEDED
# def delete_table_records(value):
#     for item in value:
#         db.session.delete(item)
#     db.session.commit()


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
