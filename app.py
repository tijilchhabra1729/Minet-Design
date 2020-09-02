from make import app, db
from make.forms import RegistrationForm, LoginForm, UpdateUserForm, CowForm, UpdateCow
from make.models import User, Cow
from picture_handler import add_profile_pic
from flask import render_template, request, url_for, redirect, flash, abort
from flask_login import current_user, login_required, login_user, logout_user
import datetime
from sqlalchemy import asc, desc
import stripe


public_key = 'pk_test_6pRNASCoBOKtIshFeQd4XMUh'

stripe.api_key = "sk_test_BQokikJOvBiI2HlWgH4olfQ2"


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():

        user = User(name=form.name.data,
                    username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        if form.picture.data is not None:
            id = user.id
            pic = add_profile_pic(form.picture.data, id)
            user.profile_image = pic
            db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = ''
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is not None and user.check_password(form.password.data):

            login_user(user)
            flash('Log in Success!')

            next = request.args.get('next')
            if next == None or not next[0] == '/':
                next = url_for('index')
            return redirect(next)
        elif user is not None and user.check_password(form.password.data) == False:
            error = 'Wrong Password'
        elif user is None:
            error = 'No such login Please create one'

        return redirect(url_for('all_cow'))
    return render_template('login.html', form=form, error=error)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    pic = current_user.profile_image
    form = UpdateUserForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.username = form.username.data

        if form.picture.data is not None:
            id = current_user.id
            pic = add_profile_pic(form.picture.data, id)
            current_user.profile_image = pic

        flash('User Account Created')
        db.session.commit()
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    profile_image = url_for('static', filename=current_user.profile_image)
    return render_template('account.html', profile_image=profile_image, form=form, pic=pic)


@app.route('/allcows', methods=['GET', 'POST'])
@login_required
def all_cow():
    form = CowForm()
    if form.validate_on_submit():
        cow = Cow(name=form.name.data,
                  age=form.age.data,
                  weight=form.weight.data,
                  urine=form.urine.data,
                  userid=current_user.id)
        db.session.add(cow)
        db.session.commit()
        return redirect('allcows')
    mycow = Cow.query.filter_by(
        userid=current_user.id).order_by(Cow.id.desc())
    return render_template('all_cow.html', cow=mycow, form=form)

@app.route('/cowupdate' , methods = ['GET' , 'POST'])
@login_required
def update():
    cow = Cow.query.first()
    form = UpdateCow()
    if cow is None:
        abort(404)
    elif  current_user.id != cow.user.id:
        abort(403)
    else:
        if form.validate_on_submit():
            cow.name = form.name.data
            cow.age = form.age.data
            cow.urine = form.urine.data
            cow.weight = form.weight.data
            flash('Rent Account Updated')
            db.session.commit()
            return redirect(url_for('all_rental'))
        elif request.method == 'GET':
             form.name.data = cow.name
             form.age.data = cow.age
             form.urine.data = cow.urine
             form.weight.data = cow.weight
        return render_template('update.html' , cow = cow , form = form)

@app.route('/delete',methods = ['GET','POST'])
@login_required
def delete(rent_id):
    cow = Rent.query.get_or_404(id)
    if cow.user != current_user:
        abort(403)
    db.session.delete(cow)
    db.session.commit()
    flash('Cow deleted')
    return redirect(url_for('allcows'))


@app.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    render_template('buy.html')


@app.route('/pay', methods=['GET', 'POST'])
def pay():
    return render_template('payment.html', public_key=public_key)


@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')


@app.route('/payment', methods=['POST'])
@login_required
def payment():
    # CUSTOMER INFORMATION
    customer = stripe.Customer.create(email=request.form['stripeEmail'],
                                      source=request.form['stripeToken'])

    # CHARGE/PAYMENT INFORMATION
    charge = stripe.Charge.create(
        customer=customer.id,
        amount=1999,
        currency='usd',
        description='Booking'
    )

    return redirect(url_for('thankyou'))


if __name__ == '__main__':
    app.run(debug=True)
