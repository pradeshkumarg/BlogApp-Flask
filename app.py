from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

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

# Articles = Articles();

# root
@app.route("/")
def index():
    return render_template('home.html')

# layout route
@app.route("/layout")
def layouts():
    return render_template('layout.html')

# about route
@app.route("/about")
def about():
        return render_template('about.html')

# articles route
@app.route("/articles")
def articles():
        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        result = cur.execute('SELECT id,title FROM articles')

        if(result>0):
            Articles = cur.fetchall()

        return render_template('articles.html', articles = Articles)

# article route
@app.route("/article/<string:id>")
def article(id):
        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        result = cur.execute('SELECT * FROM articles where id = %s',(id))

        if(result>0):
            article = cur.fetchone()

        return render_template('article.html', article = article);

# register form class
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

# check if the user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
        # if(session['logged_in'] == True):
            return f(*args,**kwargs)
        else:
            flash("Unauthorized, Please login","danger")
            return redirect(url_for('login'))
    return wrap

# dashboard route
@app.route("/dashboard")
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

# logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear();
    flash("You are now logged out","success")
    return redirect(url_for('login'))

# Article form class
class ArticleForm(Form):
    title = StringField('Title', validators=[validators.Length(min=1,max=200)])
    body  = TextAreaField('Body', validators=[validators.Length(min=30)])

# add article route
@app.route("/add_article", methods = ['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if(request.method == 'POST' and form.validate()):
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # execute
        cur.execute('INSERT into articles(title,body,author) values(%s,%s,%s)',(title,body,session['username']))

        # Commit
        mysql.connection.commit()

        # close connection
        cur.close()

        flash("Article Created Successfully","success")
        return redirect(url_for('dashboard'))

    return render_template("add_article.html",form=form)

if __name__ == '__main__':
    app.run(debug=True);
