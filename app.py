from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__);

# setting secret key
app.secret_key = 'lol'
app.config['SESSION_TYPE'] = 'filesystem'

# config mysql
app.config["MYSQL_HOST"]='localhost'
app.config["MYSQL_USER"]='root'
app.config["MYSQL_PASSWORD"]=''
app.config["MYSQL_DB"]='myapp'
app.config["MYSQL_CURSORCLASS"]='DictCursor' # for Dictionary

# init mysql
mysql = MySQL(app)

Articles = Articles();

@app.route("/")
def index():
    return render_template('home.html')

@app.route("/layout")
def layouts():
    return render_template('layout.html')

@app.route("/about")
def about():
        return render_template('about.html')

@app.route("/articles")
def articles():
        return render_template('articles.html', articles = Articles)

@app.route("/article/<string:id>")
def article(id):
        return render_template('article.html', id = id);

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

# logout
@app.route("/logout")
def logout():
    session.clear();
    flash("You are now logged out","success")
    return redirect(url_for('login'))

class RegisterForm(Form):
    name = StringField('Name', validators=[validators.Length(min=1,max=50)])
    username  = StringField('Username', validators=[validators.Length(min=4,max=25)])
    email = StringField('Email',validators=[validators.Length(min=6,max=50)])
    password = PasswordField('Password',[validators.DataRequired(),
        validators.EqualTo('confirm',message="Passwords do not match !!")
    ])
    confirm = PasswordField('Confirm Password')

@app.route("/register",methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name =form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()

        result = cur.execute('SELECT * FROM users where username = %s',[username])
        #Check if username is valid
        if(result>0):
            flash('Username Already Taken','danger')
            # error = 'Username Already Taken'
            return redirect(url_for('register'))

        # execute query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))

        # Commit to debug
        mysql.connection.commit()

        # close connection
        cur.close()

        flash("You are now registered and can log in", 'success')
        return redirect(url_for('login'))
    return render_template("register.html",form=form)

# User login
@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute('SELECT * FROM users where username = %s',[username])

        if(result>0):
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #compare password
            if sha256_crypt.verify(password_candidate,password):
                # password matched
                app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                app.logger.info('PASSWORD DOES NOT MATCHED')
                error = 'Invalid login'
                return render_template('login.html',error=error)
        else:
            app.logger.info("No such user")
            error = 'Username not found'
            return render_template('login.html',error=error)

        # close connection
        cur.close()
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True);
