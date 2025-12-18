import os, secrets, requests
from functools import wraps
from flask import render_template,url_for,request,flash,session,redirect,jsonify,current_app
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from datetime import datetime
from werkzeug.utils import secure_filename
from quicklet import app,csrf
from quicklet.form import AgentLoginForm, AgentRegistrationForm, AddListingForm,AgentProfileForm
from quicklet.models import db,Admin,Agent,Apartment,Category,State,Lga,Apartment_pic,User,Booking,Review

# this is the folder where the saved apartments of the agents will go to 
UPLOAD_FOLDER= os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)






@app.get("/auth/google/login/agent")
def agent_google_login():
    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI_AGENT"],
        "response_type": "code",
        "scope": "openid email profile"
    }

    google_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode(params)
    )

    return redirect(google_url)


# THis is the google callback route

@app.get("/auth/google/callback/agent")
def agent_google_callback():
    random_password = secrets.token_urlsafe(16)
    agent_pwd_hash = generate_password_hash(random_password)
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
            "redirect_uri": current_app.config["GOOGLE_REDIRECT_URI_AGENT"],
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
        agent = Agent.query.filter(
            (Agent.agent_email == google_email) | (Agent.google_id == google_id)
        ).first()

        if not agent:
            # Split full name into first and last
            if google_name:
                fname, lname = google_name.split()[0], " ".join(google_name.split()[1:])
            else:
                fname, lname = "Google", "User"

            agent = Agent(
                agent_fname=fname,
                agent_lname=lname,
                agent_email=google_email,
                google_id=google_id,
                g_profile_pic=google_pic,
                agent_pwd=agent_pwd_hash,  # No password for Google login
                agent_regdate=datetime.utcnow()
            )

            db.session.add(agent)
            db.session.commit()

        # Step 4: Issue JWT
        session.pop("useronline", None)  # Ensure no user session
        session['agentonline'] = agent.agent_id
        return redirect(url_for('agent_dashboard'))

    except Exception as e:
        return jsonify({"error": "Google login failed", "details": str(e)}), 500















@app.route('/agent/register/', methods=['GET','POST'])
def agent_register():
    agf= AgentRegistrationForm()
    if request.method=='GET':
        return render_template('user/agentregister.html',agf=agf)
    else:
        if agf.validate_on_submit():
            #retrive form data
            firstname=agf.firstname.data #same as request.form.get(firstname)
            lastname=agf.lastname.data
            email=agf.email.data
            phone=agf.phone.data
            password=agf.password.data
            to_be_stored = generate_password_hash(password)
            #steps to insert to db | from quicklet.models import db, User
            a=Agent(agent_fname=firstname, agent_lname=lastname, agent_phone=phone, agent_email=email,agent_pwd=to_be_stored) #instantiate
            try:
                db.session.add(a) #step2 to add
                db.session.commit() #step3 commit
                flash('An account has been created for you, Please Login', category='success')
                return redirect(url_for('agent_login'))
            except:
                #save errormsg in flash and redirect to registration page
                flash('Email is taken', category='error')
                return redirect(url_for('agent_register'))
        else:
            return render_template('user/signup.html',agf=agf)


@app.route('/agent/login/', methods=["GET", "POST"])
def agent_login():
    alog = AgentLoginForm()

    # If already logged in → redirect
    if 'agentonline' in session:
        return redirect(url_for('agent_dashboard'))

    # POST = handle form submission
    if request.method == "POST":
        if alog.validate_on_submit():
            email = alog.email.data
            password = alog.password.data

            # Check if agent exists
            agent = Agent.query.filter_by(agent_email=email).first()

            if agent:
                if check_password_hash(agent.agent_pwd, password):
                    session['agentonline'] = agent.agent_id
                    flash('You are now logged in', 'success')
                    return redirect(url_for('agent_dashboard'))
                else:
                    flash('Incorrect password', 'error')
                    return redirect(url_for('agent_login'))
            else:
                flash('Email not found', 'error')
                return redirect(url_for('agent_login'))
        else:
            flash('Please fill in all fields correctly', 'error')
            return redirect(url_for('agent_login'))

    # GET = show login form
    return render_template('user/agentlogin.html', alog=alog)



        
# This is the agent dashboard
@app.route('/agent/dashboard/')

def agent_dashboard():
    ag = session.get('agentonline')
    a=Agent.query.get(ag)
    adeets=Agent.query.get(ag)
    reviews = Review.query.join(Apartment).filter(Apartment.apartment_userid == ag).all()



    if not a:
        # user is not an agent → show message or redirect
        flash("You must be logged in as an agent to access this page.", "warning")
        return redirect(url_for('agent_login'))


    if not ag:
        # user is not an agent → show message or redirect
        flash("You must be logged in as an agent to access this page.", "warning")
        return redirect(url_for('agent_login'))
    apic= Apartment_pic.query.all()
    
    my_apartments = Apartment.query.filter_by(apartment_agent_id=ag).all()
    return render_template('user/agentdashboard_page.html',a=a,adeets=adeets,my_apartments=my_apartments, apic=apic,ag=ag,reviews=reviews)


@app.route('/mylistingpage/')
def my_listing_page():
    
    a=Agent.query.get(session['agentonline'])
    ag = session.get('agentonline')
    user_id = session.get('agentonline')
    my_apartments = Apartment.query.filter_by(apartment_agent_id=ag).all()

    return render_template('user/mylisting.html',a=a,user_id=user_id,my_apartments=my_apartments)



@app.route('/agent/edit/profile/')
def agent_edit_profile():
    proform=AgentProfileForm()
    if session.get('agentonline') != None:
        adeets=Agent.query.get(session['agentonline'])
        proform.email.data=adeets.agent_email #to dusplay the email
        proform.phone.data=adeets.agent_phone#to dusplay the email
        proform.agent_bio.data=adeets.agent_bio #this is to display the phone munber

        return render_template('user/agentedit_profile.html',proform=proform,adeets=adeets)
    else:
        flash('You must be logged in as an agent to view this page', category='warning')
        return redirect(url_for('agent_login'))

@app.post('/agent/update/profile/')
def agent_update_profile():
    proform=AgentProfileForm()
    if session.get('agentonline') !=None:
        adeets=Agent.query.get(session['agentonline'])
        if proform.validate_on_submit():
            fname=proform.fname.data
            lname=proform.lname.data
            phone=proform.phone.data
            email=proform.email.data
            bio=proform.agent_bio.data
            
            pic=proform.agent_avatar.data
            if pic:
                filename=proform.agent_avatar.data.filename
                _,ext=os.path.splitext(filename)
                newname=secrets.token_hex(10)+ext
                pic.save('quicklet/static/uploads/'+newname)
                adeets.agent_avatar=newname

            # update db via orm
            adeets.agent_fname=fname
            adeets.agent_lname=lname
            adeets.agent_phone=phone
            adeets.agent_email=email
            adeets.agent_bio=bio
            db.session.commit()
            flash('Profile updated Successfully', category='success')
            return redirect(url_for('agent_edit_profile'))
        else:          
                return render_template('user/agentedit_profile.html',proform=proform,adeets=adeets)
    else:
            flash('You must be logged in to view this page', category='errormsg')
            return redirect(url_for('agent_login'))




# #this is the listing route and page 
# @app.route('/listingpage/')

# def listing_page():
    
#     a=Agent.query.get(session['agentonline'])
#     user_id = session.get('agentonline')
#     my_apartments = Apartment.query.filter_by(apartment_userid=user_id).all()
    
#     # if session.get('qlclin') !=None:
#     #     return render_template('listingpage.html')
#     return render_template('user/listingpage.html',a=a,user_id=user_id,my_apartments=my_apartments)




# this is the my bookings route
@app.route('/view/bookings/')
def my_bookings():
    agent_id = session.get('agentonline')
    agent = Agent.query.get(agent_id)

    if not agent:
        flash("You must be logged in as an agent.", "warning")
        return redirect(url_for('agent_login'))

    # Get all apartments for this agent
    my_apartments = Apartment.query.filter_by(apartment_agent_id=agent_id).all()

    # Prepare a list of dicts with apartment + bookings info
    apartment_bookings = []
    for apt in my_apartments:
        # Get paid bookings for this apartment
        bookings = Booking.query.filter_by(booking_apt_id=apt.apartment_id, booking_status='paid').all()
        booked_users = []
        for b in bookings:
            user = User.query.get(b.apartment_user_id)
            booked_users.append({
                "name": user.user_fname.capitalize() if user else "Unknown",
                "booking_date": b.booking_date_created.strftime("%Y-%m-%d")
            })
        apartment_bookings.append({
            "apartment": apt,
            "bookings_count": len(bookings),
            "booked_users": booked_users
        })

    return render_template('user/mybookings.html', agent=agent, apartment_bookings=apartment_bookings)


# this is the add apartment route latest 18 

@app.route('/add/apt/', methods=['GET', 'POST'])
def add_apt():
    add = AddListingForm()
    a = Agent.query.get(session.get('agentonline'))

    if not a:
        flash("You must be logged in as an agent.", "danger")
        return redirect(url_for('agent_login'))

    categories = Category.query.all()
    states = State.query.all()

    if add.validate_on_submit():

        # 1. Determine if published or draft
        status = 'active' if request.form.get('action') == 'publish' else 'inactive'

        # 2. Create the apartment (images added later)
        apartment = Apartment(
            
            apartment_stateid=request.form.get('state'),
            apartment_lga_id=request.form.get('lga'),
            apartment_category_id=request.form.get('category_id'),
            apartment_max_guests = add.max_guests.data,
            apartment_agent_id=a.agent_id,

            apartment_title=add.title.data,
            apartment_address=f" {add.area.data or ''},{add.city.data}",
            apartment_description=add.description.data,
            apartment_price=add.price.data,
            apartment_status=status
        )

        db.session.add(apartment)
        db.session.commit()   # now apartment.apartment_id exists

        # 3. Save uploaded images (NO FEATURED IMAGE LOGIC AT ALL)
        uploaded_files = add.photos.data

        if len(uploaded_files) < 3:
            flash("You must upload at least 3 photos.", "danger")
            return redirect(url_for("add_apt"))

        if uploaded_files:
            for file in uploaded_files:
                if file:
                    # Extract extension (.jpg, .png, etc.)
                    _, ext = os.path.splitext(file.filename)

                    # Generate random name
                    newname = secrets.token_hex(10) + ext

                    # Build save path (inside your project)
                    save_path = os.path.join(
                        "quicklet/static/uploads/apartments/",newname)

                    # Save file to disk
                    file.save(save_path)

                    # Save record to DB
                    pic = Apartment_pic(
                        apt_image="uploads/apartments/" + newname,
                        apt_apartment_userid=apartment.apartment_id
                    )
                    db.session.add(pic)

        db.session.commit()

        flash(f"Apartment saved as {status}.", "success")
        return redirect(url_for('my_bookings'))

    return render_template('user/add_apartments.html',add=add,a=a,categories=categories,states=states)


# This is the delete route
@csrf.exempt
@app.route('/apartment/delete/<int:apartment_id>', methods=['POST'])
def delete_apartment(apartment_id):
    # Get the current logged-in user's ID
    agent_id = session.get('agentonline')
    
    # Fetch the apartment from the database
    apartment = Apartment.query.get_or_404(apartment_id)
    
    # Ensure that only the owner can delete their apartment
    if apartment.apartment_agent_id != agent_id:
        flash("You are not authorized to delete this apartment.", "danger")
        return redirect(url_for('my_listing_page'))
    
    # Delete the apartment
    db.session.delete(apartment)
    db.session.commit()
    
    flash("Apartment deleted successfully.", "success")
    return redirect(url_for('my_listing_page'))



# this is to edit the apartmnet 


@app.route('/apartment/edit/<int:apartment_id>', methods=['GET', 'POST'])
def edit_apartment(apartment_id):
    agent_id = session.get('agentonline')
    a = Agent.query.get(agent_id)

    if not a:
        flash("You must be logged in as an agent.", "danger")
        return redirect(url_for('agent_login'))

    apartment = Apartment.query.get_or_404(apartment_id)

    if apartment.apartment_agent_id != agent_id:
        flash("You are not authorized to edit this apartment.", "danger")
        return redirect(url_for('my_listing_page'))

    # Pre-fill the form with apartment data
    form = AddListingForm(obj=apartment)
    form.photos.validators = []  # allow empty on edit

    # Pre-fill city and area separately
    if request.method == "GET":
        try:
            form.description.data = apartment.apartment_description  # optional
            form.title.data = apartment.apartment_title
            city, area = apartment.apartment_address.split(",", 1)
            form.city.data = city.strip()
            form.area.data = area.strip()
        except:
            form.city.data = apartment.apartment_address
            form.area.data = ""

        form.price.data = float(apartment.apartment_price) if apartment.apartment_price else None

    # Fetch categories and states
    categories = Category.query.all()
    states = State.query.all()

    # Fetch LGAs for the apartment's state
    lgas = Lga.query.filter_by(state_id=apartment.apartment_stateid).all()

    if form.validate_on_submit():
        apartment.apartment_title = form.title.data
        apartment.apartment_description = form.description.data
        apartment.apartment_price = form.price.data
        apartment.apartment_address = f"{form.city.data}, {form.area.data or ''}"

        # Update category, state, and LGA
        apartment.apartment_category_id = request.form.get('category_id')
        apartment.apartment_stateid = request.form.get('state')
        apartment.apartment_lga_id = request.form.get('lga')

        # Handle new uploaded photos (optional)
        uploaded_files = form.photos.data
        if uploaded_files:
            for file in uploaded_files:
                if file:
                    _, ext = os.path.splitext(file.filename)
                    newname = secrets.token_hex(10) + ext
                    save_path = os.path.join(
                        "quicklet/static/uploads/apartments/", newname
                    )
                    file.save(save_path)
                    pic = Apartment_pic(
                        apt_image="uploads/apartments/" + newname,
                        apt_apartment_userid=apartment.apartment_id
                    )
                    db.session.add(pic)

        db.session.commit()
        flash("Apartment updated successfully!", "success")
        return redirect(url_for('my_listing_page'))

    return render_template(
        "user/edit_apartments.html",
        form=form,
        apartment=apartment,
        a=a,
        categories=categories,
        states=states,
        lgas=lgas  # pass LGAs for the dropdown
    )



    # IMPORTANT
# @app.route('/apartment/edit/<int:apartment_id>', methods=['GET', 'POST'])
# def edit_apartment(apartment_id):
#     agent_id = session.get('agentonline')

#     # Authenticate
#     if not agent_id:
#         flash("Please login as an agent.", "danger")
#         return redirect(url_for('agent_login'))

#     # Fetch the apartment
#     apartment = Apartment.query.get_or_404(apartment_id)

#     # Prevent editing other agent’s apartments
#     if apartment.apartment_agent_id != agent_id:
#         flash("You are not allowed to edit this listing.", "danger")
#         return redirect(url_for('listing_page'))

#     # Pre-fill the form using obj=
#     form = AddListingForm(obj=apartment)

#     # IMPORTANT: remove FileRequired validator for edit mode
#     form.photos.validators = []   # allow empty uploads on edit

#     if form.validate_on_submit():

#         # Update main fields
#         apartment.apartment_title = form.title.data
#         apartment.apartment_description = form.description.data
#         apartment.apartment_price = form.price.data
#         apartment.apartment_address = f"{form.city.data}, {form.area.data or ''}"

#         # Save new uploaded photos (optional)
#         uploaded_files = form.photos.data
#         if uploaded_files:
#             for file in uploaded_files:
#                 if file:
#                     _, ext = os.path.splitext(file.filename)
#                     newname = secrets.token_hex(10) + ext
#                     save_path = os.path.join(
#                         "quicklet/static/uploads/apartments/",
#                         newname
#                     )
#                     file.save(save_path)

#                     new_pic = Apartment_pic(
#                         apt_image="uploads/apartments/" + newname,
#                         apt_apartment_userid=apartment.apartment_id
#                     )
#                     db.session.add(new_pic)

#         db.session.commit()
#         flash("Apartment updated successfully!", "success")
#         return redirect(url_for('listing_page'))

#     return render_template("user/edit_apartments.html", form=form, apartment=apartment)









# route to create category

@app.route('/create/cat/', methods=['GET','POST'])
def create_cat():
    cat1 = Category(category_name='Studio Apartment')
    cat2 = Category(category_name='Mini-Flat')
    cat3 = Category(category_name='1 Bedroom')
    cat4 = Category(category_name='2 Bedroom')
    cat5 = Category(category_name='3 Bedroom')
    cat6 = Category(category_name='4+ Bedroom')
    cat7 = Category(category_name='Duplex')
    cat8 = Category(category_name='Bungalow')
    db.session.add_all([cat1,cat2,cat3,cat4,cat5,cat6,cat7,cat8])
    db.session.commit()
    return 'Data Created'



# route to create state 

@app.route('/create/states/')
def create_states():
    states_list = ['Lagos', 'Abuja']

    for s in states_list:
        state = State(state_name=s)
        db.session.add(state)

    db.session.commit()
    return 'States created successfully!'


# route to create Loval Goverments


@app.route('/create/lgas/')
def create_lgas():
    # Lagos LGAs
    lagos_state = State.query.filter_by(state_name='Lagos').first()
    lagos_lgas = [
    'Agege', 'Ajeromi-Ifelodun', 'Alimosho', 'Amuwo-Odofin', 'Apapa',
    'Badagry', 'Epe', 'Eti-Osa', 'Ibeju-Lekki', 'Ifako-Ijaiye',
    'Ikeja', 'Ikorodu', 'Kosofe', 'Lagos Island', 'Lagos Mainland',
    'Mushin', 'Ojo', 'Oshodi-Isolo', 'Shomolu', 'Surulere'
                ]
    for lga_name in lagos_lgas:
        lga = Lga(lga_name=lga_name, state_id=lagos_state.state_id)
        db.session.add(lga)

    # Abuja LGAs
    abuja_state = State.query.filter_by(state_name='Abuja').first()
    abuja_lgas = ['Gwagwalada', 'Kwali', 'Abaji', 'Bwari', 'Kuje', 'Municipal']
    for lga_name in abuja_lgas:
        lga = Lga(lga_name=lga_name, state_id=abuja_state.state_id)
        db.session.add(lga)

    db.session.commit()
    return 'LGAs for Lagos and Abuja created successfully!'


# ajax route to get apartments | this is Json

# @app.route('/get-lgas/<state_id>')
# def get_lgas(state_id):
#     lgas = Lga.query.filter_by(state_id=state_id).all()
#     data = [{"id": lga.lga_id, "name": lga.lga_name} for lga in lgas]
#     return jsonify(data)


# This returns Html in the option tag

@app.route('/get/lgas/')
def get_lgas():
    state_id = request.args.get('state_id')
    lgas = Lga.query.filter_by(state_id=state_id).all()

    html = "<option value=''>Select LGA</option>"
    for l in lgas:
        html += f"<option value='{l.lga_id}'>{l.lga_name}</option>"

    return html



@app.route('/agent/earnings/')
def agent_earnings():
    # Ensure agent is logged in
    agent_id = session.get('agentonline')
    if not agent_id:
        return redirect(url_for('agent_login'))

    # 1. Get all apartments belonging to this agent
    apartments = Apartment.query.filter_by(apartment_agent_id=agent_id).all()
    apartment_ids = [apt.apartment_id for apt in apartments]

    # If agent has no apartments yet
    if not apartment_ids:
        return render_template(
            'user/agent_earnings.html',
            total_earned=0,
            pending_earnings=0,
            total_paid_bookings=0,
            bookings=[],
            earnings_per_apartment={}
        )

    # 2. Get all bookings for agent's apartments
    bookings = Booking.query.filter(
        Booking.booking_apt_id.in_(apartment_ids)
    ).order_by(Booking.booking_date_created.desc()).all()

    # 3. Split into paid and pending
    paid_bookings = [b for b in bookings if b.booking_status == 'paid']
    pending_bookings = [b for b in bookings if b.booking_status != 'paid']

    # 4. Calculate Totals
    total_earned = sum(b.booking_price for b in paid_bookings)
    pending_earnings = sum(b.booking_price for b in pending_bookings)
    total_paid_bookings = len(paid_bookings)

    # 5. Calculate earnings per apartment
    earnings_per_apartment = {}
    for apt in apartments:
        apt_paid = [b for b in paid_bookings if b.booking_apt_id == apt.apartment_id]
        earnings_per_apartment[apt] = sum(b.booking_price for b in apt_paid)

    return render_template(
        'user/myearnings.html',
        total_earned=total_earned,
        pending_earnings=pending_earnings,
        total_paid_bookings=total_paid_bookings,
        bookings=bookings,
        apartments=apartments,
        earnings_per_apartment=earnings_per_apartment
    )
















    # this is my logout route 
@app.get('/agent/logout/')
def agent_logout():
    if session.get('agentonline') !=None:
        session.pop('agentonline')
        session.clear()
    flash('You have logged out successfully.', category='success')
    return redirect(url_for('agent_login'))





