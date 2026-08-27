from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import DateTimeLocalField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    role = SelectField("Role", choices=[("candidate", "Candidate"), ("recruiter", "Recruiter"), ("tester", "Tester"), ("admin", "Admin")], validators=[DataRequired()])
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    role = SelectField("Role", choices=[("candidate", "Candidate")], validators=[DataRequired()])
    submit = SubmitField("Create account")


class JobForm(FlaskForm):
    title = StringField("Job title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=5000)])
    requirements = TextAreaField("Requirements", validators=[DataRequired(), Length(max=5000)])
    status = SelectField("Status", choices=[("open", "Open"), ("closed", "Closed")], validators=[DataRequired()])
    submit = SubmitField("Publish job")


class ApplicationForm(FlaskForm):
    candidate_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    candidate_email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    resume = FileField("Resume", validators=[FileRequired(), FileAllowed(["pdf", "doc", "docx"], "PDF, DOC, or DOCX only.")])
    submit = SubmitField("Submit application")


class InterviewForm(FlaskForm):
    interview_at = DateTimeLocalField("Interview time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    submit = SubmitField("Schedule interview")


class AlertForm(FlaskForm):
    alert_type = StringField("Alert type", validators=[DataRequired(), Length(max=80)])
    severity = SelectField("Severity", choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Log issue")


class UserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    role = SelectField("Role", choices=[("admin", "Admin"), ("recruiter", "Recruiter"), ("tester", "Tester")], validators=[DataRequired()])
    submit = SubmitField("Save user")
