from flask_wtf import FlaskForm
from wtforms import StringField, EmailField,PasswordField,SubmitField,TelField,TextAreaField,FileField,DateField, RadioField,DecimalField,IntegerField,SelectField,MultipleFileField,SelectMultipleField
from wtforms.validators import DataRequired,Email,Length,EqualTo,Optional,NumberRange
from flask_wtf.file import FileAllowed,FileRequired

class UserForm(FlaskForm):
    username= StringField('Username',validators=[DataRequired()])
    password= StringField('Password',validators=[DataRequired()])
    submit= StringField('Login',validators=[DataRequired()])

    class Meta:
        csrf = True
        csrf_time_limit = 3600

class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    # phone = TelField("Phone Number", validators=[DataRequired(), Length(min=7, max=15)])
    password = PasswordField('Password',validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')
    

class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()] )
    submit = SubmitField('Login')



class AgentRegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = TelField("Phone Number", validators=[DataRequired(), Length(min=7, max=15)])
    password = PasswordField('Password',validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')


class AgentLoginForm(FlaskForm):
    email = StringField('Username',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()] )
    submit = SubmitField('Login')

class AgentProfileForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = TelField("Phone Number", validators=[DataRequired(), Length(min=7, max=15)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    agent_bio= TextAreaField('Bio', validators=[DataRequired()])
    agent_avatar= FileField('Image', validators=[Optional(),FileAllowed(['jpg','jpeg','png'], 'Images only!!')])
    submit = SubmitField('Update Profile')

class ProfileForm(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = TelField("Phone Number", validators=[DataRequired(), Length(min=5, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    user_avatar= FileField('Image', validators=[Optional(),FileAllowed(['jpg','jpeg','png'], 'Images only!!')])
    submit = SubmitField('Update Profile')

class ContactForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email',validators=[DataRequired(), Email()])
    phone = TelField("Phone Number", validators=[DataRequired(), Length(min=5, max=20)])
    complain_text= TextAreaField('Message', validators=[DataRequired()])
    contact_method = RadioField('Preferred Contact Method',choices=[('call', 'Call'), ('text', 'Text')],validators=[DataRequired()])


class AdminLoginForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()] )
    submit = SubmitField('Login')



class AddListingForm(FlaskForm):
    # Core fields
    title = StringField('Title', validators=[DataRequired(), Length(max=30)])
    # short_desc = StringField('Short description', validators=[DataRequired()])
    description = TextAreaField('Full description', validators=[Optional()])
    
    price = DecimalField('Price (per night)', validators=[DataRequired(), NumberRange(min=0)])
    currency = SelectField('Currency', choices=[('NGN','Naira (NGN)'), ('USD','USD')], default='NGN')
    
    # category = SelectField('Category', choices=[('apartment','Apartment'), ('studio','Studio'), ('house','House')], validators=[DataRequired()])
    beds = IntegerField('Bedrooms', validators=[Optional(), NumberRange(min=0)])
    
    city = StringField('City', validators=[DataRequired()])
    area = StringField('Area / Neighbourhood', validators=[Optional()])
    
    
    # Availability
    min_nights = IntegerField('Minimum nights', validators=[Optional(), NumberRange(min=1)])
    max_guests = IntegerField('Max guests', validators=[Optional(), NumberRange(min=1)])
    
    # File uploads
    photos = MultipleFileField('Photos')



    # , validators=[
    #     FileRequired(message="Please upload at least one image"),
    #     FileAllowed(['jpg','jpeg','png'], message="Images only!")
    # ]
    



    # # Featured image index (optional, set in backend after upload)
    # featured_index = SelectField('Featured image', choices=[], validators=[Optional()])


class BookingForm(FlaskForm):
    check_in = DateField("Check-in", validators=[DataRequired()])
    check_out = DateField("Check-out", validators=[DataRequired()])
    guests = SelectField(
        "Guests",
        choices=[("1", "1 Guest"), ("2", "2 Guests"), ("3", "3 Guests"), ("4", "4 Guests")],
        validators=[DataRequired()]
    )
    submit = SubmitField("Book Now")


class ReviewForm(FlaskForm):
    review_comment = TextAreaField('Your Review', validators=[DataRequired()])
    review_rating_number = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')
