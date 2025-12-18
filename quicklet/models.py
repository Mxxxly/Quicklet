from datetime import datetime 
from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()



class User(db.Model):
    user_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    user_fname= db.Column(db.String(100),nullable=False )
    user_lname= db.Column(db.String(100),nullable=False )
    user_email=db.Column(db.String(100),unique=True, nullable=False)
    user_avatar = db.Column(db.String(255))
    user_phone = db.Column(db.String(20),nullable=True)
    user_regdate= db.Column(db.DateTime(),default=datetime.utcnow)
    user_pwd= db.Column(db.String(255), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # optional
    g_profile_pic = db.Column(db.String(255), nullable=True) 

    apartments = db.relationship('Apartment', back_populates='user', lazy='dynamic')
    bookings = db.relationship('Booking', back_populates='user', cascade="all, delete-orphan", lazy='dynamic')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='user', lazy='dynamic')
    contacts = db.relationship('ContactUs', back_populates='user', lazy='dynamic')


class Agent(db.Model):
    agent_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    agent_fname= db.Column(db.String(100),nullable=False )
    agent_lname= db.Column(db.String(100),nullable=False )
    agent_email=db.Column(db.String(100),unique=True, nullable=False)
    agent_avatar = db.Column(db.String(255))
    agent_phone = db.Column(db.String(20),nullable=True)
    agent_bio = db.Column(db.Text)

    agent_status = db.Column(db.Enum('active', 'inactive'), default='active')
    agent_regdate= db.Column(db.DateTime(),default=datetime.utcnow)
    agent_pwd= db.Column(db.String(255), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # optional
    g_profile_pic = db.Column(db.String(255), nullable=True) 

    apartments = db.relationship('Apartment', back_populates='agent')
    



class Admin(db.Model):
    admin_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    admin_username = db.Column(db.String(100),nullable=False)
    admin_email=db.Column(db.String(100),unique=True, nullable=False)
    last_login = db.Column(db.DateTime(), default=datetime.utcnow)
    admin_pwd = db.Column(db.String(255),nullable=False)



class Apartment(db.Model):


    apartment_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    apartment_userid = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    apartment_stateid = db.Column(db.Integer, db.ForeignKey('state.state_id'))
    apartment_address = db.Column(db.String(150), nullable=False)
    apartment_title = db.Column(db.String(150), nullable=False) 
    apartment_description = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(255)) 
    apartment_price = db.Column(db.Numeric(12, 2))
    apartment_max_guests = db.Column(db.Integer)
    apartment_status = db.Column(db.Enum('active', 'inactive'), default='active')
    apartment_date_created_at = db.Column(db.DateTime, default=datetime.utcnow)
    apartment_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    apartment_category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    apartment_agent_id = db.Column(db.Integer, db.ForeignKey('agent.agent_id'))
    apartment_lga_id = db.Column(db.Integer, db.ForeignKey('lga.lga_id'))
    



    agent = db.relationship('Agent', back_populates='apartments')
    category = db.relationship('Category', back_populates='apartments')
    user = db.relationship('User', back_populates='apartments')
    # bookings = db.relationship('Booking', back_populates='apartment', lazy='dynamic')
    bookings = db.relationship('Booking',back_populates='apartment', cascade="all, delete-orphan", foreign_keys='Booking.booking_apt_id',lazy='dynamic')

    @property
    def bookings_count(self):
        return self.bookings.count()
    reviews = db.relationship('Review', back_populates='apartment', lazy='dynamic')
    pictures = db.relationship('Apartment_pic',back_populates='apartment',cascade="all, delete-orphan")
    state = db.relationship('State', back_populates='apartments')
    lga = db.relationship('Lga')




class Apartment_pic(db.Model):
    apt_pic_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    apt_image = db.Column(db.String(255))
    apt_apartment_userid = db.Column(db.Integer, db.ForeignKey('apartment.apartment_id'), nullable=False)

    apartment = db.relationship('Apartment', back_populates='pictures')



class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)

    apartments = db.relationship('Apartment', back_populates='category')


class Lga(db.Model):
    lga_id = db.Column(db.Integer, primary_key=True, autoincrement=True,nullable=False)
    lga_name = db.Column(db.String(50), nullable=False,default='') 
    state_id = db.Column(db.Integer,db.ForeignKey('state.state_id'),default="0",nullable=False)

class State(db.Model):
   state_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
   state_name= db.Column(db.String(100),nullable=False )

   apartments = db.relationship('Apartment', back_populates='state', lazy='dynamic')
   lgas = db.relationship('Lga', backref='state', lazy='dynamic')


class Property(db.Model):
   property_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
   property_name= db.Column(db.String(100),nullable=False )
   property_user_id=db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)



class Booking(db.Model):
    booking_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    apartment_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete="CASCADE"),  nullable=False)
    booking_ref = db.Column(db.Integer, unique=True, nullable=False, index=True)
    booking_apt_id = db.Column(db.Integer, db.ForeignKey('apartment.apartment_id'))
    booking_checkin = db.Column(db.String(150), nullable=False)
    booking_checkout = db.Column(db.String(150), nullable=False)
    booking_guests = db.Column(db.Integer, default=1)
    booking_price = db.Column(db.Numeric(12, 2))
    booking_data = db.Column(db.Text)
    booking_status = db.Column(db.Enum('pending', 'paid', 'failed', 'cancelled'),default='pending', nullable=False)
    booking_date_created = db.Column(db.DateTime, default=datetime.utcnow)
    booking_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='bookings')
    apartment = db.relationship('Apartment', back_populates='bookings')
    payments = db.relationship('Payment', back_populates='booking', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='booking', lazy='dynamic')


class Payment(db.Model):
    pay_id = db.Column(db.Integer, primary_key=True)
    pay_amt = db.Column(db.Float)
    pay_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    pay_booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'), nullable=True)
    pay_ref = db.Column(db.String(100))
    pay_method = db.Column(db.Enum('paystack','bank_transfer', 'debit_card', 'credit_card'))
    pay_status = db.Column(db.Enum('pending', 'failed', 'paid'))
    pay_data = db.Column(db.JSON)
    pay_date = db.Column(db.DateTime, default=datetime.utcnow)


    user = db.relationship('User', back_populates='payments')
    booking = db.relationship('Booking', back_populates='payments')


class Review(db.Model):
    review_id = db.Column(db.Integer(),primary_key=True, autoincrement=True)
    review_comment= db.Column(db.String(100),nullable=False )
    review_date_created = db.Column(db.DateTime, default=datetime.utcnow)
    review_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    review_apt_id = db.Column(db.Integer, db.ForeignKey('apartment.apartment_id'), nullable=False)
    review_booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'), nullable=False)
    review_rating_number= db.Column(db.Text, nullable=False)

    user = db.relationship('User', back_populates='reviews')
    apartment = db.relationship('Apartment', back_populates='reviews')
    booking = db.relationship('Booking', back_populates='reviews')



class ContactUs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    complain_text = db.Column(db.Text, nullable=False)
    contact_method = db.Column(db.String(20), nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)


    user = db.relationship('User', back_populates='contacts')


class SavedApartment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
    apartment_id = db.Column(db.Integer, db.ForeignKey("apartment.apartment_id"))
    date_saved = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="saved_apartments")
    apartment = db.relationship("Apartment")








    
