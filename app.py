import re
import main
import database.db as db
from flask import Flask, request, session, redirect, url_for, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = ''

DB_HOST = ""
DB_NAME = ""
DB_USER = ""
DB_PASS = ""

frs = db.FRSDatabase(DB_NAME, DB_PASS)


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'loggedin' in session:
        if request.method == 'POST':
            if request.form.get('generate') == 'РЕКОМЕНДОВАТЬ':
                return redirect(url_for('recommendations'))
        return render_template('home.html')
    return redirect(url_for('login'))


@app.route('/recommendations/', methods=['GET', 'POST'])
def recommendations():
    if 'loggedin' in session:
        account = frs.get_current_user(session['id'])
        recs = main.start(frs, account['vk_id'])
        if request.method == 'POST':
            if request.form.get('like') == '✔':
                fid = request.form['film-id']
                print(fid)
                frs.rate_film(account['vk_id'], fid, True)
                return redirect(url_for('recommendations'))
            if request.form.get('dislike') == '✘':
                fid = request.form['film-id']
                print(fid)
                frs.rate_film(account['vk_id'], fid, False)
                return redirect(url_for('recommendations'))
            if request.form.get('add-film') == 'ДОБАВИТЬ':
                fid = request.form['add-film-id']
                print(fid)
                frs.add_film_to_list(account['vk_id'], fid)
                return redirect(url_for('recommendations'))
        return render_template('recommendations.html', username=session['username'], recs=recs)
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        print(password)

        account = frs.check_if_username_exists(username)

        if account:
            password_rs = account['password']
            print(password_rs)
            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                return redirect(url_for('home'))
            else:
                flash('Неправильный логин или пароль')
        else:
            flash('Неправильный логин или пароль')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'vk' in request.form:
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        vkid = request.form['vk']

        _hashed_password = generate_password_hash(password)

        account = frs.check_if_username_exists(username)

        print(account)

        pid, sn = main.check_vk_id(vkid)

        person_id = frs.check_vk_id_exists(pid)

        if account:
            flash('Аккаунт с таким логином уже существует!')
        elif person_id:
            flash('VK ID уже привязан к другому аккаунту!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Логин должен состоять из латинских букв и цифр')
        elif not username or not password or not vkid or not fullname:
            flash('Заполните все поля')
        elif sn == 0 and pid == 0:
            flash('Недействительный VK ID')
        else:
            frs.insert_user(fullname, username, _hashed_password, pid, sn)
            return redirect(url_for('home'))
    elif request.method == 'POST':
        flash('Заполните форму!')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' in session:
        account = frs.get_current_user(session['id'])
        history = frs.get_defined_user_recommendations(account['vk_id'])
        flist = frs.get_films_list(account['vk_id'])
        for i in history:
            if i['rating']:
                i['rating'] = '✔'
            else:
                i['rating'] = '✘'
        if request.method == 'POST':
            if request.form.get('like') == '✔':
                fid = request.form['film-id']
                print(fid)
                frs.rate_film(account['vk_id'], fid, True)
                return redirect(url_for('profile'))
            if request.form.get('dislike') == '✘':
                fid = request.form['film-id']
                print(fid)
                frs.rate_film(account['vk_id'], fid, False)
                return redirect(url_for('profile'))
            if request.form.get('add-film') == 'ДОБАВИТЬ':
                fid = request.form['add-film-id']
                print(fid)
                frs.add_film_to_list(account['vk_id'], fid)
                return redirect(url_for('profile'))
        return render_template('profile.html', account=account, history=history, flist=flist)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
