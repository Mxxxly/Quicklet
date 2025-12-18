from functools import wraps
from flask import render_template,url_for,request,flash,session,redirect
from werkzeug.security import generate_password_hash, check_password_hash
from quicklet import app
from quicklet.form import AdminLoginForm
from quicklet.models import db,Admin,User,Agent,Apartment,Booking


    # login required 
def login_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if session.get('adminonline')!=None:
            return f(*args,**kwargs)
        else:
            flash('You need to be logged in as admin to see this page',category='adminerror')
        return redirect('/admin/login/')
    return wrapper


    # This is my admin home page route 
@app.route('/admin/',methods=['GET','POST'])
@login_required
def admin_home():
    admin_id = session.get('adminonline')

    if not admin_id:
        flash("You must be logged in as an admin.", "danger")
        return redirect(url_for('admin_login'))

    # Fetch all data
    all_apartments = Apartment.query.all()
    all_users = User.query.all()
    all_agents = Agent.query.all()
    total_apartments = Apartment.query.count()
    total_users = User.query.count()
    total_agents = Agent.query.count()
    total_bookings = Booking.query.count()

    return render_template('admin/dashboard.html',apartments=all_apartments,users=all_users,agents=all_agents,total_apartments=total_apartments,total_bookings=total_bookings,total_users=total_users,total_agents=total_agents)


    # manage agents route

@app.route('/admin/manage-agents')
def manage_agents():
    if not session.get('adminonline'):
        return redirect(url_for('admin_login'))

    agents = Agent.query.all()

    return render_template('admin/manage_agents.html', agents=agents)

# manage users route 

@app.route('/admin/manage-users')
def manage_users():
    if not session.get('adminonline'):
        return redirect(url_for('admin_login'))

    users = User.query.all()

    return render_template('admin/manage_users.html', users=users)

# manage apartments route


@app.route('/admin/manage-apartments')
def manage_apartments():
    if not session.get('adminonline'):
        return redirect(url_for('admin_login'))

    apartments = Apartment.query.all()

    return render_template('admin/manage_apartments.html', apartments=apartments)




# route to delete apartment 
@app.route('/admin/delete_apartment/<int:apartment_id>', methods=['POST'])
def admin_delete_apartment(apartment_id):

    admin_id = session.get('adminonline')
    if not admin_id:
        flash("Admin permissions required.", "danger")
        return redirect(url_for('admin_login'))

    apt = Apartment.query.get_or_404(apartment_id)
    
    db.session.delete(apt)
    db.session.commit()
    
    flash("Apartment deleted successfully.", "success")
    return redirect(url_for('manage_apartments'))

# route to delete users 

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):

    admin_id = session.get('adminonline')
    if not admin_id:
        flash("Admin permissions required.", "danger")
        return redirect(url_for('admin_login'))

    user = User.query.get_or_404(user_id)
    
    db.session.delete(user)
    db.session.commit()
    
    flash("User deleted successfully.", "success")
    return redirect(url_for('manage_users'))


# route to delete agents 
@app.route('/admin/delete_agent/<int:agent_id>', methods=['POST'])
def admin_delete_agent(agent_id):

    admin_id = session.get('adminonline')
    if not admin_id:
        flash("Admin permissions required.", "danger")
        return redirect(url_for('admin_login'))

    agent = Agent.query.get_or_404(agent_id)
    
    db.session.delete(agent)
    db.session.commit()
    
    flash("Agent deleted successfully.", "success")
    return redirect(url_for('manage_agents'))




    # This is my admin login route 
@app.route('/admin/login/', methods=['POST', 'GET'])
def admin_login():
    adminloginform=AdminLoginForm()
    if request.method=='GET':
        return render_template('admin/admin_login.html',adminloginform=adminloginform)
    else:
        if adminloginform.validate_on_submit(): #this is where they login and i validate thier details
            username=adminloginform.username.data
            password=adminloginform.password.data
            admin_details=Admin.query.filter(Admin.admin_username==username).first()

            if admin_details: #means the username is correct and they can proceed 
                stored_password=admin_details.admin_pwd
                check_password= check_password_hash(stored_password,password)
                if check_password ==True:
                    session['adminonline']=admin_details.admin_id
                    return redirect('/admin/')
                else: #comes here if the password is wrong 
                    flash('Invalid Login Password', category='adminmsg')
                    return redirect(url_for('admin_login'))
            else: #come to this if the username is wrong 
                flash('Invalid Username, Try Again', category='adminmsg')
                return redirect(url_for('admin_login'))
        else:
            return render_template('admin/admin_login.html',adminloginform=adminloginform)


        # this is my admin logout route
@app.route('/admin/logout', methods=['POST', 'GET'])
def admin_logout():
    if session.get('adminonline')!=None:
        session.pop('adminonline')   
    return redirect('/admin/login/')


# this is the route to delete a customer 
@app.get('/admin/delete/customer/')
def delete_customer():
    id = 4
    user= User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return f'Customer with the id of {id} was deleted'


# this is the route to delete  an agent 
@app.get('/admin/delete/customer/')
def delete_agent():
    id = 4
    user= Agent.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return f'Customer with the id of {id} was deleted'

@app.route('/admin/control/user/',methods=['GET','POST'])
def admin_control_user():
    u=User.query.all()
    num_of_customers = db.session.query(User).count()

    return render_template('admin/adminctrl.html',u=u,num_of_customers=num_of_customers)