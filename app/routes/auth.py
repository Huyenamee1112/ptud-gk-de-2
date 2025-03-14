import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import requests
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__)

def get_random_avatar():
    try:
        response = requests.get('https://avatar.iran.liara.run/public')
        if response.status_code == 200:
            avatar_url = response.json()['avatar']
            # Download and save avatar image
            img_response = requests.get(avatar_url)
            if img_response.status_code == 200:
                filename = f"avatar_{os.urandom(8).hex()}.png"
                avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                with open(avatar_path, 'wb') as f:
                    f.write(img_response.content)
                return filename
    except:
        return 'default.jpg'
    return 'default.jpg'

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        if form.avatar.data:
            filename = secure_filename(form.avatar.data.filename)
            form.avatar.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            user.avatar = filename
        else:
            user.avatar = get_random_avatar()
            
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index')) 