import os,secrets,requests,random,json
import jwt
from datetime import datetime, timedelta, date
from functools import wraps
from flask import render_template,redirect,request,url_for,make_response,session,flash,jsonify,current_app
import urllib.parse
from werkzeug.security import generate_password_hash, check_password_hash
from quicklet.jwt_utils import generate_jwt
from werkzeug.utils import secure_filename
from quicklet import app,csrf
from flask_wtf.csrf import validate_csrf
from quicklet.models import db,User,ContactUs,Apartment,Category,State,Lga,Agent,Booking,Payment,SavedApartment,Review
from quicklet.form import RegistrationForm, LoginForm, ContactForm , AddListingForm, ProfileForm, BookingForm,ReviewForm
from sqlalchemy import func


JWT_SECRET = app.config["JWT_SECRET"]
JWT_ALGORITHM = app.config["JWT_ALGORITHM"]
JWT_EXPIRES_MINUTES = app.config["JWT_EXPIRES_MINUTES"]

UPLOAD_FOLDER= os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#to clear cache and make it a convention to always put the route at the top
@app.after_request
def after_request(resp):
    resp.headers['Cache-Control']='no-cache,no-store,must-revalidate'
    return resp

def login_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if session.get('useronline')!=None:
            return f(*args,**kwargs)
        else:
            flash('You need to be logged in to see this page',category='error')
        return redirect('/login/')
    return wrapper






@app.get('/')
def home_page():
    pagetitle = 'Home Page'
    user = None
    agent = None
    categories = Category.query.order_by(Category.category_name).all()
    # categories = Category.query.all()
    apartments = Apartment.query.all()
    states = State.query.order_by(State.state_name).all()
    apartments = Apartment.query.all()
    contact = ContactForm()


    if session.get("useronline"):
        user = User.query.get(session["useronline"])

    if session.get("agentonline"):
        agent = Agent.query.get(session["agentonline"])


    return render_template('user/index.html',categories=categories,states=states,apartments=apartments,user=user,agent=agent,contact=contact,pagetitle=pagetitle)   



@app.get("/auth/google/login")
def google_login():
    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid email profile"
    }

    google_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode(params)
    )

    return redirect(google_url)


# THis is the google callback route

@app.get("/auth/google/callback")
def google_callback():
    random_password = secrets.token_urlsafe(16)
    user_pwd_hash = generate_password_hash(random_password)
    try:
        code = request.args.get("code")

        if not code:
            return jsonify({"error": "Authorization code not found"}), 400

        # Step 1: Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
            "grant_type": "authorization_code"
        }

        token_response = requests.post(token_url, data=data)
        token_response.raise_for_status()  # Raises exception if HTTP error

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return jsonify({"error": "Access token not received"}), 400

        # Step 2: Fetch user info from Google
        user_info_resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info_resp.raise_for_status()
        user_info = user_info_resp.json()

        google_id = user_info.get("id")
        google_email = user_info.get("email")
        google_name = user_info.get("name")
        google_pic = user_info.get("picture")

        if not google_email:
            return jsonify({"error": "Email not found in Google profile"}), 400

        # Step 3: Check if user exists in your DB
        user = User.query.filter(
            (User.user_email == google_email) | (User.google_id == google_id)
        ).first()

        if not user:
            # Split full name into first and last
            if google_name:
                fname, lname = google_name.split()[0], " ".join(google_name.split()[1:])
            else:
                fname, lname = "Google", "User"

            user = User(
                user_fname=fname,
                user_lname=lname,
                user_email=google_email,
                google_id=google_id,
                g_profile_pic=google_pic,
                user_pwd=user_pwd_hash,  # No password for Google login
                user_regdate=datetime.utcnow()
            )

            db.session.add(user)
            db.session.commit()

        # Step 4: Issue JWT
        session.pop("agentonline", None)  # Ensure no agent session
        session['useronline'] = user.user_id
        return redirect(url_for('user_dashboard'))

    except Exception as e:
        return jsonify({"error": "Google login failed", "details": str(e)}), 500



# This is important for when you want to see the json and details of the google callback success details

# @app.get("/auth/google/callback")
# def google_callback():
#     random_password = secrets.token_urlsafe(16)
#     user_pwd_hash = generate_password_hash(random_password)
#     try:
#         code = request.args.get("code")

#         if not code:
#             return jsonify({"error": "Authorization code not found"}), 400

#         # Step 1: Exchange code for tokens
#         token_url = "https://oauth2.googleapis.com/token"
#         data = {
#             "code": code,
#             "client_id": current_app.config["GOOGLE_CLIENT_ID"],
#             "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
#             "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
#             "grant_type": "authorization_code"
#         }

#         token_response = requests.post(token_url, data=data)
#         token_response.raise_for_status()  # Raises exception if HTTP error

#         token_data = token_response.json()
#         access_token = token_data.get("access_token")

#         if not access_token:
#             return jsonify({"error": "Access token not received"}), 400

#         # Step 2: Fetch user info from Google
#         user_info_resp = requests.get(
#             "https://www.googleapis.com/oauth2/v2/userinfo",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )
#         user_info_resp.raise_for_status()
#         user_info = user_info_resp.json()

#         google_id = user_info.get("id")
#         google_email = user_info.get("email")
#         google_name = user_info.get("name")
#         google_pic = user_info.get("picture")

#         if not google_email:
#             return jsonify({"error": "Email not found in Google profile"}), 400

#         # Step 3: Check if user exists in your DB
#         user = User.query.filter(
#             (User.user_email == google_email) | (User.google_id == google_id)
#         ).first()

#         if not user:
#             # Split full name into first and last
#             if google_name:
#                 fname, lname = google_name.split()[0], " ".join(google_name.split()[1:])
#             else:
#                 fname, lname = "Google", "User"

#             user = User(
#                 user_fname=fname,
#                 user_lname=lname,
#                 user_email=google_email,
#                 google_id=google_id,
#                 g_profile_pic=google_pic,
#                 user_pwd=user_pwd_hash,  # No password for Google login
#                 user_regdate=datetime.utcnow()
#             )

#             db.session.add(user)
#             db.session.commit()

#         # Step 4: Issue JWT
#         payload = {
#             "user_id": user.user_id,
#             "email": user.user_email,
#             "exp": datetime.utcnow() + timedelta(minutes=current_app.config["JWT_EXPIRES_MINUTES"])
#         }
#         token = jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm=current_app.config["JWT_ALGORITHM"])

#         # Step 5: Return JWT + user info
#         return jsonify({
#             "message": "Login successful",
#             "token": token,
#             "user": {
#                 "id": user.user_id,
#                 "fname": user.user_fname,
#                 "lname": user.user_lname,
#                 "email": user.user_email,
#                 "avatar": user.g_profile_pic
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": "Google login failed", "details": str(e)}), 500












# @app.get("/auth/google/callback")
# def google_callback():
#     code = request.args.get("code")

#     if not code:
#         return jsonify({"error": "Authorization code not found"}), 400

#     token_url = "https://oauth2.googleapis.com/token"

#     data = {
#         "code": code,
#         "client_id": current_app.config["GOOGLE_CLIENT_ID"],
#         "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
#         "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI"],
#         "grant_type": "authorization_code"
#     }

#     token_response = requests.post(token_url, data=data)

#     token_data = token_response.json()

#     return jsonify(token_data)




# @app.get("/auth/google/callback")
# def google_callback():
#     code = request.args.get("code")

#     if not code:
#         return jsonify({"error": "Authorization code not found"}), 400

#     return jsonify({
#         "message": "Google redirected successfully",
#         "authorization_code": code
#     })


@app.get('/check/email/')
def check_email():
    email = request.args.get('demail')
    record= User.query.filter(User.user_email==email).first()
    if record:
        return 'Email is taken'
    else:
        return 'Email is available'


@app.route('/register/', methods=['GET','POST'])
def user_register():
    regform=RegistrationForm()
    if request.method=='GET':
        return render_template('user/signup.html',regform=regform)
    else:
        if regform.validate_on_submit():
            #retrive form data
            firstname=regform.firstname.data #same as request.form.get(firstname)
            lastname=regform.lastname.data
            email=regform.email.data
            # phone=regform.phone.data
            password=regform.password.data
            to_be_stored = generate_password_hash(password)
            #steps to insert to db | from quicklet.models import db, User
            u=User(user_fname=firstname, user_lname=lastname, user_email=email,user_pwd=to_be_stored) #instantiate
            try:
                db.session.add(u) #step2 to add
                db.session.commit() #step3 commit
                flash('An account has been created for you, Please Login', category='success')
                return redirect(url_for('user_login'))
            except:
                #save errormsg in flash and redirect to registration page
                flash('Email is taken', category='error')
                return redirect(url_for('user_register'))
        else:
            return render_template('user/signup.html',regform=regform)

@app.route('/login/',methods=["GET","POST"])
def user_login():
    user = None
    agent = None
    
    if session.get('useronline'):
        user = User.query.get(session['useronline'])

    if session.get('agentonline'):
        agent = Agent.query.get(session['agentonline'])
    log = LoginForm()
    if request.method=='GET':
        return render_template('user/login.html',log=log,user=user,agent=agent)
    else:
        if log.validate_on_submit():
            # to get the form data 
            email = log.email.data
            password= log.password.data
            record= User.query.filter(User.user_email==email).first()

            if record: #when it gets to this stage it means the email is correct now this conditions verifies the password 
                stored_hash=record.user_pwd
                userid=record.user_id
                checkpwd= check_password_hash(stored_hash,password)
                if checkpwd==True: # to get to this stage it means email and password is true
                    session['useronline']=userid
                    flash('You are now logged in', category='success')
                    return redirect(url_for('user_dashboard'))
                else: #the email is not correct 
                    flash('The password is not correct, Try Again', 'error')
                    return redirect(url_for('user_login'))
            else:
                flash('Your email is incorrect, Try Again', 'error')
                return redirect(url_for('user_login'))
        else:
            flash('Please fill out all required fields correctly.', 'error')
            return redirect(url_for('user_login'))
            


@app.get('/logout/')
def user_logout():
    if session.get('useronline') !=None:
        session.pop('useronline')
        session.clear()
    flash('You have logged out successfully.', category='success')
    return redirect(url_for('user_login'))


# #to create customers and add them to the database 
# @app.get('/create/user/')
# def create_user():
#     user2=User(user_fname='Mimi', user_lname='Mark Alabi', user_email='mimi@gmail.com', user_phone='78678854', pwd='mimiff')
#     user3=User(user_fname='Emma', user_lname='OD', user_email='eo@gmail.com', user_phone='76678854', pwd='shshs')
#     user4=User(user_fname='Alvan', user_lname='aq', user_email='aq@gmail.com', user_phone='75978854', pwd='alvan')
#     # this below is to add a single user informations to the database
#     # db.session.add(user1) 
#     # db.session.commit()

#     # This is to add multiple users to the db 
#     db.session.add_all([user2,user3,user4]) 
#     db.session.commit()
#     return f'Customers has been created'

# This is tiy get users 
@app.get('/get/user/')
def get_user():
    users=User.query.all()
    num_of_customers = db.session.query(User).count()
    # the proper way to do it
    name=db.session.query(User).get(2)
    print(name)
    return render_template('user/users.html',users=users,num_of_customers=num_of_customers)

# This route is to update the user information 
@app.get('/update/user/')
def update_user():
    id= 2
    user=User.query.get(id)
    user.user_fname='Michaela'
    user.user_email='Mm@gmail.com'
    db.session.commit()
    return f'Customer with the id of :{id} has been updated in our database'

# this route is to delete infos in the database | moved to agent route
# @app.get('/delete/customer/')
# def delete_customer():
#     id = 4
#     user= User.query.get(id)
#     db.session.delete(user)
#     db.session.commit()
#     return f'Customer with the id of {id} was deleted'







@app.route('/filter/apartments/', methods=['GET'])
def filter_apartments():
    """
    Filter apartments using any combination of:
      - location (text search against apartment_address)
      - category (category_id from Category table)
      - state (state_id)
      - lga (lga_id)
    The form on the banner submits these as GET parameters:
      ?location=...&category=...&state=...&lga=...
    """

    # read query params (strings or None)
    user = None
    agent= None
    location = request.args.get('location', type=str)
    category_id = request.args.get('category')   # category id as string
    state_id = request.args.get('state')        # state id as string
    lga_id = request.args.get('lga')            # lga id as string

    # start a base query
    query = Apartment.query

    if session.get("useronline"):
        user = User.query.get(session["useronline"])

    if session.get("agentonline"):
        agent = Agent.query.get(session["agentonline"])

    # text search on the address/title (case-insensitive)
    if location:
        # adjust the field you search on if you store location differently
        query = query.filter(Apartment.apartment_address.ilike(f"%{location}%"))

    # filter by category id (if provided)
    if category_id:
        try:
            query = query.filter(Apartment.apartment_category_id == int(category_id))
        except ValueError:
            # ignore invalid id
            pass

    # filter by state id
    if state_id:
        try:
            query = query.filter(Apartment.apartment_stateid == int(state_id))
        except ValueError:
            pass

    # filter by lga id
    if lga_id:
        try:
            query = query.filter(Apartment.apartment_lga_id == int(lga_id))
        except ValueError:
            pass

    # finally execute
    apartments = query.order_by(Apartment.apartment_date_created_at.desc()).all()

    # also send categories and states back so the page can re-render selects if needed
    # categories = Category.query.order_by(Category.category_name).all()
    categories = Category.query.all()
    states = State.query.order_by(State.state_name).all()

    return render_template(
        "user/properties.html",
        apartments=apartments,
        categories=categories,
        states=states,
        agent=agent,
        user=user
    )



@app.route('/apartment/<int:apartment_id>', methods=['GET', 'POST'])
def apartment_display(apartment_id):
    """
    Show apartment profile and booking form (WTForms).
    - GET: render page with form pre-filled (if needed).
    - POST: validate form; if valid redirect to confirm-booking page (separate page).
    """
    user = None
    agent = None
    apartment_saved = False
    paid_booking = None
    conflicting_booking = None
    review_count = Review.query.filter_by(review_apt_id=apartment_id).count()


    if session.get("useronline"):
        user = User.query.get(session["useronline"])
        apartment_saved = SavedApartment.query.filter_by(user_id=user.user_id,apartment_id=apartment_id).first() is not None
        today = date.today()



        paid_booking = Booking.query.filter(
            Booking.apartment_user_id == user.user_id,
            Booking.booking_apt_id == apartment_id,
            Booking.booking_status.in_(["pending", "paid"]),
            Booking.booking_checkout >= today
        ).first()
        # paid_booking = Booking.query.filter_by(apartment_user_id=user.user_id,booking_apt_id=apartment_id,booking_status='paid').first()

    if session.get("agentonline"):
        agent = Agent.query.get(session["agentonline"])
    # 1) Fetch apartment from DB, or 404 if not found
    apartment = Apartment.query.get_or_404(apartment_id)

    # 2) Instantiate the WTForm (includes CSRF automatically)
    form = BookingForm()

    # 3) Dynamically set guests choices based on apartment data (if available)
    #    Example: if apartment.max_guests exists, populate choice list from 1..max_guests.
    max_guests = getattr(apartment, 'apartment_max_guests', None) or getattr(apartment, 'max_guests', None)
    if max_guests:
        # create tuples: (value, label)
        form.guests.choices = [(str(i), f"{i} guest{'s' if i > 1 else ''}") for i in range(1, int(max_guests) + 1)]
    else:
        # default choices
        form.guests.choices = [('1', '1 guest'), ('2', '2 guests'), ('3', '3 guests'), ('4', '4 guests')]

    gent = apartment.agent
    regdate = gent.agent_regdate  # already in your DB

    if regdate:
        now = datetime.utcnow()
        delta = now - regdate
        hosting_months = delta.days // 30   # convert days → months
    else:
        hosting_months = 0

    # 4) If the form is submitted and valid, redirect to confirmation page (separate flow)
    if form.validate_on_submit():
        # convert date objects to ISO strings for passing via query parameters (or use session)
        check_in = form.check_in.data.isoformat()
        check_out = form.check_out.data.isoformat()
        guests = form.guests.data

        conflicting_booking = Booking.query.filter(
            Booking.booking_apt_id == apartment_id,
            Booking.booking_status == 'paid',
            Booking.booking_checkin < check_out,
            Booking.booking_checkout > check_in
        ).first()


        if conflicting_booking:
            flash("Apartment is unavailable for the selected dates. Please choose different dates.","danger")
            # return redirect(url_for('apartment_display', apartment_id=apartment_id))
            return render_template(
                'user/apartmentprofile.html',
                apartment=apartment,
                form=form,
                user=user,
                agent=agent,
                apartment_saved=apartment_saved,
                paid_booking=paid_booking,
                hosting_months=hosting_months,
                review_count=review_count,
                conflicting_booking=conflicting_booking
            )



        if paid_booking:
            flash(f"You already have an active booking for this apartment until {paid_booking.booking_checkout}.","danger")
            return redirect(url_for('apartment_display', apartment_id=apartment_id))

        # Redirect to confirm page with the booking details as query params
        return redirect(url_for('confirm_booking',
                                apartment_id=apartment_id,
                                check_in=check_in,
                                check_out=check_out,
                                guests=guests,conflicting_booking=conflicting_booking))

    # 5) GET or invalid form: show template with the form (errors shown inline)
    return render_template('user/apartmentprofile.html',
                           apartment=apartment,
                           form=form,user=user,agent=agent,apartment_saved=apartment_saved,
                           paid_booking=paid_booking,hosting_months=hosting_months,
                           review_count=review_count,conflicting_booking=conflicting_booking
                           )      

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    data = request.get_json()

    apartment_id = data.get('apartment_id')
    check_in = datetime.fromisoformat(data.get('check_in')).date()
    check_out = datetime.fromisoformat(data.get('check_out')).date()

    conflicting_booking = Booking.query.filter(
        Booking.booking_apt_id == apartment_id,
        Booking.booking_status == 'paid',
        Booking.booking_checkin < check_out,
        Booking.booking_checkout > check_in
    ).first()

    if conflicting_booking:
        return jsonify({
            "available": False,
            "from": conflicting_booking.booking_checkin.isoformat(),
            "to": conflicting_booking.booking_checkout.isoformat()
        })

    return jsonify({"available": True})

@app.route('/confirm/booking')
def confirm_booking():
    """
    Page to show booking confirmation before finalizing payment or saving to DB.
    Receives apartment_id, check_in, check_out, guests via query parameters.
    """

    agent = None



    if session.get("agentonline"):
        agent = Agent.query.get(session["agentonline"])

    # Get data from URL query parameters
    apartment_id = request.args.get('apartment_id', type=int)
    check_in = request.args.get('check_in')  # ISO string
    check_out = request.args.get('check_out')  # ISO string
    guests = request.args.get('guests')

    #  Fetch apartment from DB
    apartment = Apartment.query.get_or_404(apartment_id)

    # 3️ Optionally fetch logged-in user (if needed)
    user = None
    if session.get('useronline'):
        user = User.query.get(session['useronline'])

    # Pass all data to template
    return render_template('user/confirm_booking.html',
                           apartment=apartment,
                           check_in=check_in,
                           check_out=check_out,
                           guests=guests,
                           user=user,agent=agent)


@app.route('/finalize/booking', methods=['POST'])
def final_confirmation():

    # User must be logged in
    if not session.get("useronline"):
        session['pending_booking'] = {
            "apartment_id": request.form.get('apartment_id'),
            "check_in": request.form.get('check_in'),
            "check_out": request.form.get('check_out'),
            "guests": request.form.get('guests')
        }
        return redirect(url_for('user_login'))

    user = User.query.get(session['useronline'])

    #  POST data
    apartment_id = request.form.get('apartment_id', type=int)
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    guests = request.form.get('guests', type=int)

    apartment = Apartment.query.get_or_404(apartment_id)

    #  Nights calculation
    d1 = datetime.strptime(check_in, "%Y-%m-%d")
    d2 = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (d2 - d1).days

    if nights <= 0:
        flash("Invalid date selection", "danger")
        return redirect(url_for('confirm_booking'))

    #  Total price
    total_amount = nights * apartment.apartment_price

    # YOUR LOGIC: simple random reference
    refno = int(random.random() * 100000000)
    session['ref'] = refno   # store in session

    booking_ref = refno  # save into DB

    #  Create booking
    new_booking = Booking(
        apartment_user_id=user.user_id,
        booking_ref=booking_ref,
        booking_apt_id=apartment.apartment_id,
        booking_checkin=check_in,
        booking_checkout=check_out,
        booking_guests=guests,
        booking_price=total_amount,
        booking_status='pending'
    )

    db.session.add(new_booking)
    db.session.commit()

    # Show payment confirmation page
    return render_template(
        'user/payconfirm.html',
        apartment=apartment,
        user=user,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        nights=nights,
        total_amount=total_amount,
        booking=new_booking,
        booking_ref=booking_ref
    )


@app.route('/paystack', methods=['GET','POST'])
@app.route('/paystack/', methods=['GET','POST'])  # trailing slash safe
def paystack_step1():
    if not session.get('useronline'):
        flash('You must be logged in', category='errormsg')
        return redirect(url_for('user_login'))

    ref = session.get('ref')
    if not ref:
        flash('Please review payment page', category='errormsg')
        return redirect(url_for('confirm_booking'))

    # Fetch booking and prepare Paystack payload
    booking = Booking.query.filter_by(booking_ref=ref).first()
    if not booking:
        flash('Booking not found', category='errormsg')
        return redirect(url_for('confirm_booking'))

    try:
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk_test_f703ed91e65546ea1981ae553a470af6b61c7fb7"
        }
        data = {
            "amount": int(booking.booking_price * 100),  # Paystack expects kobo
            "reference": str(ref),
            "email": booking.user.user_email,
            "callback_url": url_for("paystack_step2", _external=True)  # must match server port
        }

        rsp = requests.post(url, headers=headers, data=json.dumps(data))
        jsonrsp = rsp.json()
        if jsonrsp.get('status') is True:
            return redirect(jsonrsp['data']['authorization_url'])
        else:
            flash('Error connecting to Paystack', category='errormsg')
            return redirect(url_for('confirm_booking'))
    except Exception as e:
        flash(f'Error connecting to Paystack: {str(e)}', category='errormsg')
        return redirect(url_for('confirm_booking'))
    


@app.route("/paystack/landing", methods=['GET'])
@app.route("/paystack/landing/", methods=['GET'])
def paystack_step2():
    # Paystack always returns reference in URL
    ref = request.args.get('reference') or session.get('ref')

    if not ref:
        flash("Missing payment reference", "error")
        return redirect(url_for("user_dashboard"))

    try:
        url = f"https://api.paystack.co/transaction/verify/{ref}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk_test_f703ed91e65546ea1981ae553a470af6b61c7fb7"
        }
        rsp = requests.get(url, headers=headers)
        jsonrsp = rsp.json()

        booking = Booking.query.filter_by(booking_ref=ref).first()
        if not booking:
            flash("Booking not found", "error")
            return redirect(url_for("user_dashboard"))

        if jsonrsp.get('status') is True:
            booking.booking_status = 'paid'

            new_payment = Payment(
                pay_amt=float(booking.booking_price),
                pay_user_id=booking.apartment_user_id,
                pay_booking_id=booking.booking_id,
                pay_ref=ref,
                pay_method='paystack',
                pay_status='paid',
                pay_data=json.dumps(jsonrsp)  # convert to string
            )
            db.session.add(new_payment)
            db.session.commit()

            return redirect(url_for("booking_confirmation", booking_ref=ref))

        else:
            booking.booking_status = 'failed'
            booking.booking_data = json.dumps(jsonrsp)
            db.session.commit()

            flash("Payment failed", "error")
            return redirect(url_for("user_dashboard"))

    except Exception as e:
        flash(f"Verification error: {e}", "error")
        return redirect(url_for("user_dashboard"))



@app.route('/booking/confirmation/<int:booking_ref>/')
def booking_confirmation(booking_ref):
    """
    Show booking confirmation page after successful payment.
    """
    user = None
    agent = None

    if session.get("useronline"):
        user = User.query.get(session["useronline"])

    if session.get("agentonline"):
        agent = Agent.query.get(session["agentonline"])

    booking = Booking.query.filter_by(booking_ref=booking_ref).first_or_404()
    apartment = Apartment.query.get(booking.booking_apt_id)

    return render_template('user/booking_confirmation.html',
                           booking=booking,
                           user=user,
                           agent=agent,apartment=apartment)


@app.route('/submit_review/<int:apartment_id>', methods=['POST'])
@csrf.exempt
def submit_review(apartment_id):
    #  User must be logged in
    user_id = session.get("useronline")
    if not user_id:
        flash("You must be logged in to submit a review.", "danger")
        return redirect(url_for('user_login'))

    user = User.query.get(user_id)
    apartment = Apartment.query.get_or_404(apartment_id)

    # Get data from form
    review_comment = request.form.get("review_comment")
    review_rating_number = request.form.get("review_rating_number")

    # Check if user has a paid booking for this apartment
    paid_booking = Booking.query.filter_by(
        apartment_user_id=user.user_id,
        booking_apt_id=apartment_id,
        booking_status='paid'
    ).first()

    if not paid_booking:
        flash("You can only review apartments you have paid for.", "danger")
        return redirect(url_for('apartment_display', apartment_id=apartment_id))

    # Save review
    new_review = Review(
        review_comment=review_comment,
        review_rating_number=review_rating_number,
        review_user_id=user.user_id,
        review_apt_id=apartment_id,
        review_booking_id=paid_booking.booking_id
    )
    db.session.add(new_review)
    db.session.commit()

    flash("Thank you for your review!", "success")
    return redirect(url_for('apartment_display', apartment_id=apartment_id))



# This is my dashboard route 
@app.route('/dashboard/')
@login_required
def user_dashboard():
    u=User.query.get(session['useronline'])
    udeets=User.query.get(session['useronline'])
    user_id = session['useronline']

    # FETCH THE USER'S SAVED APARTMENTS
    saved_apartments = SavedApartment.query.join(Apartment).filter(SavedApartment.user_id == session["useronline"],).all()
    # saved_apartments = SavedApartment.query.filter_by(user_id=user_id).all()
    # saved_apt_count = SavedApartment.query.filter_by(user_id=user_id).count()
    saved_apt_count = SavedApartment.query.join(Apartment).filter(SavedApartment.user_id == user_id).count()
    # Only count unique apartments
    # saved_apt_count = SavedApartment.query.filter_by(user_id=user_id).distinct(SavedApartment.apartment_id).count()
    # this is using func import from sqlalchemy
    # saved_apt_count = db.session.query(
    #     func.count(SavedApartment.apartment_id.distinct())
    # ).filter_by(user_id=user_id).scalar()

    # FETCH THE USER'S BOOKINGS
    bookings = Booking.query.filter_by(apartment_user_id=user_id).order_by(Booking.booking_date_created.desc()).all()
    pending_payments = Booking.query.filter_by(
        apartment_user_id=user_id, 
        booking_status='pending'
    ).all()
    total_pending = sum([b.booking_price for b in pending_payments]) if pending_payments else 0
    paid_booking_count = Booking.query.filter_by(apartment_user_id=user_id, booking_status='paid').count()


    
    return render_template('user/dashboard_page.html',u=u,udeets=udeets,bookings=bookings,saved_apartments=saved_apartments,saved_apt_count=saved_apt_count,total_pending=total_pending,paid_booking_count=paid_booking_count)


@app.route('/dashboard/bookings/')
def booked_apt():
    u = User.query.get(session['useronline'])
    user_id = session['useronline']

    # Fetch only paid bookings for this user
    bookings = Booking.query.filter_by(apartment_user_id=user_id, booking_status='paid').order_by(Booking.booking_date_created.desc()).all()

    return render_template('user/bookedapt.html', u=u, bookings=bookings)

@app.route('/dashboard/reservations/')
@login_required
def my_reservations():
    user_id = session['useronline']
    u = User.query.get(user_id)

    # Fetch all bookings for the user, ordered by date
    bookings = Booking.query.filter_by(apartment_user_id=user_id) \
                            .order_by(Booking.booking_date_created.desc()).all()

    return render_template('user/my_reservations.html', u=u, bookings=bookings)


@app.route('/contact/', methods=["GET", "POST"])
# @login_required
def contact():
        contact=ContactForm()
        if contact.validate_on_submit():
            firstname = contact.firstname.data
            email = contact.email.data
            comp_text= contact.complain_text.data
            contact_method=contact.contact_method.data
            phone = contact.phone.data
            user_id = session.get('useronline')
            if user_id==None:
                flash("You must be logged in to send a message", category="error")
                return redirect(url_for('user_login'))
            co=ContactUs(firstname=firstname, contact_user_id=user_id, email=email, complain_text=comp_text, contact_method=contact_method,phone=phone)
            db.session.add(co)
            db.session.commit()
            flash('Your message has been sent succesfully', category= 'success')
            return redirect(url_for('contact'))
        return render_template('user/contact.html',contact=contact)




@app.route('/apartments/')
def apartments():
    user = None
    agent = None
    category_id = request.args.get("category", type=int)
    categories = Category.query.order_by(Category.category_name).all()
    # categories = Category.query.all()
    apartments = Apartment.query.all()
    states = State.query.order_by(State.state_name).all()
    apartments = Apartment.query.all()
        # base query
    query = Apartment.query

    if category_id:
        query = query.filter(Apartment.apartment_category_id == category_id)

    apartments = query.order_by(Apartment.apartment_date_created_at.desc()).all()


    if session.get("useronline"):
        user = User.query.get(session["useronline"])

    if session.get("agentonline"):
        agent = Agent.query.get(session["agentonline"])
    return render_template('user/apartments.html',user=user,agent=agent,categories=categories,states=states,apartments=apartments,selected_category=category_id)



@app.route('/apartments/profile/')
def apartments_profile():
    return render_template('user/apartmentprofile.html')


@app.route('/aboutus/')
def about_us():
    user = None
    agent = None
    if session.get('useronline'):
        user = User.query.get(session['useronline'])

    if session.get('agentonline'):
        agent = Agent.query.get(session['agentonline'])
    return render_template('user/aboutus.html',user=user,agent=agent)


@app.route('/save_apartment/<int:apt_id>', methods=['POST'])
def save_apartment(apt_id):
    if not session.get('useronline'):
        return jsonify({"error": "not_logged_in"}), 401

    user_id = session['useronline']

    saved = SavedApartment.query.filter_by(
        user_id=user_id,
        apartment_id=apt_id
    ).first()

    if saved:
        db.session.delete(saved)
        db.session.commit()
        return jsonify({"status": "removed"})   # UNSAVED
    else:
        new_saved = SavedApartment(
            user_id=user_id,
            apartment_id=apt_id
        )
        db.session.add(new_saved)
        db.session.commit()
        return jsonify({"status": "added"})    


@csrf.exempt
@app.route("/toggle_save", methods=["POST"])
def toggle_save():
    if not session.get("useronline"):
        return jsonify({"status": "login_required"})

    user_id = session["useronline"]
    apartment_id = request.json.get("apartment_id")

    # Check if saved before
    existing = SavedApartment.query.filter_by(
        user_id=user_id,
        apartment_id=apartment_id
    ).first()

    if existing:
        # REMOVE SAVE
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"status": "removed"})
    else:
        # ADD SAVE
        new_save = SavedApartment(
            user_id=user_id,
            apartment_id=apartment_id
        )
        db.session.add(new_save)
        db.session.commit()
        return jsonify({"status": "saved"})



@app.route('/edit/profile/')
def edit_profile():
    proform=ProfileForm()
    if session.get('useronline') != None:
        udeets=User.query.get(session['useronline'])
        proform.email.data=udeets.user_email #to dusplay the email
        proform.phone.data=udeets.user_phone #this is to display the phone munber
        return render_template('user/edit_profile.html',proform=proform,udeets=udeets)
    else:
        flash('You must be logged in to view this page', category='warning')
        return redirect(url_for('user_login'))
    





@app.post('/update/profile/')
def update_profile():
    proform=ProfileForm()
    if session.get('useronline') !=None:
        udeets=User.query.get(session['useronline'])
        if proform.validate_on_submit():
            fname=proform.fname.data
            lname=proform.lname.data
            phone=proform.phone.data
            email=proform.email.data
            
            pic=proform.user_avatar.data
            if pic:
                filename=proform.user_avatar.data.filename
                _,ext=os.path.splitext(filename)
                newname=secrets.token_hex(10)+ext
                pic.save('quicklet/static/uploads/'+newname)
                udeets.user_avatar=newname

            # update db via orm
            udeets.user_fname=fname
            udeets.user_lname=lname
            udeets.user_phone=phone
            udeets.user_email=email
            db.session.commit()
            flash('Profile updated Successfully', category='success')
            return redirect(url_for('edit_profile'))
        else:          
            return render_template('user/edit_profile.html',proform=proform,udeets=udeets)
    else:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('user_login'))
    






@app.route('/test-images/')
def test_images():
    apartments = Apartment.query.all()
    for a in apartments:
        print(a.apartment_image)  # shows DB path
    return "Check console for paths"