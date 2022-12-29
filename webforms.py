from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FileField, SelectField
from wtforms.validators import DataRequired, NumberRange, Regexp


class LoginForm(FlaskForm):
    user_name = StringField("Username", validators=[DataRequired()], render_kw={"placeholder": "Enter Username"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={"placeholder": "Enter Password"})
    submit = SubmitField("Login")


class CreateOrder(FlaskForm):
    name = StringField("Enter Name:", validators=[DataRequired()])
    choices = [
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        ('option3', 'Option 3')
    ]
    order_type = SelectField('Label', choices=choices, validators=[DataRequired()])
    count = IntegerField("Enter Number Of Items:", validators=[DataRequired(), NumberRange(min=1, message='Must enter a number greater than 0')])
    submit = SubmitField("Submit")


class CreateMachine(FlaskForm):
    name = StringField("Enter Name:", validators=[DataRequired()])
    equipment_capacity = IntegerField("Enter The Capacity Of Equipment:", validators=[DataRequired(), NumberRange(min=1,message='Must enter a number greater than 0')])
    available_hours = IntegerField("Enter Available Hours Of machine:", validators=[DataRequired(), NumberRange(min=1,message='Must enter a number greater than 0')])
    submit = SubmitField("Submit")


class UploadForm(FlaskForm):
    file_name = StringField("Enter Desired File Name:", validators=[DataRequired(), Regexp(r'^[A-Za-z0-9\s]+$', message='Field must contain only English letters, numbers, and whitespaces')])
    file = FileField("Upload a File: ", validators=[DataRequired(), FileAllowed(['csv'], message='Error! Please upload CSV file')])
    submit = SubmitField("Upload")
