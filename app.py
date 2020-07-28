from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
# importing the custom module
#from data_articles import articles_data
from functools import wraps

# Init the application
app = Flask(__name__)

# Configure the MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'blogtesting'

# Setting the pointer to write queries. By default Cursor will give tuple so we are converting that Dictionary
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Init MYSQL_DB
mysql = MySQL(app)

# Check if the user is logged out and hide the URL's for access
def is_logged_out(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Start or Home route
@app.route('/')
def home():
    return render_template('home.html')

# About route
@app.route('/about')
def about():
    return render_template('about.html')

# Assgining the articles_data to the variable
#get_articles = articles_data()

# Articles route
@app.route('/articles')
def articles():
    # Create a connectin
    cur = mysql.connection.cursor()

    # Execute the query
    result = cur.execute("SELECT * FROM articles")

    if result > 0:
        articles = cur.fetchall()
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Article Found'
        return render_template('articles.html', msg=msg)

    # Close the connection
    cur.close()


# Single Article route
@app.route('/articles/<string:id>/')
def single_article(id):
    # Establish connection
    cur = mysql.connection.cursor()

    # Fetching article based on id
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)

# Edit route for editing the article
@app.route('/edit_article/<string:id>/', methods=['GET', 'POST'])
@is_logged_out
def edit_article(id):
    # Establish the connectin
    cur = mysql.connection.cursor()

    # Fetching the article for edit
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])

    article = cur.fetchone()

    # Get a Form
    form = ArticlesForm(request.form)

    # Populate the value into the form
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        # Taking the input from the user modified one
        title = request.form['title']
        body = request.form['body']

        # Updating the article
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))

        # Commiting it to the DB
        mysql.connection.commit()

        # Close the connectin
        cur.close()
        flash('Articles Updated successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)



# User Registration field class
class RegistrationForm(Form):
    # Registration form field
    name = StringField('Name', [validators.DataRequired(), validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.DataRequired(), validators.Length(min=6, max=50)])
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Create a register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        # We are taking the input from the browser and assigning it to the respective variables
        name = form.name.data
        email = form.email.data
        username = form.username.data
        # Encrypting the password
        password = sha256_crypt.encrypt(str(form.password.data))

        # Establishing the connection to the
        cur = mysql.connection.cursor()

        # Inserting the values by executing the query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commiting to the data base
        mysql.connection.commit()

        # Close the connection

        cur.close()

        # Flash message for successful registration with category success
        flash('Registered successfully and you can log in now', 'success')

        # Redirecting to the different URL
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # Getting username and password from the users
        username = request.form['username']
        password_candidate = request.form['password']

        # Init DB connection
        cur = mysql.connection.cursor()

        # Fetching user information
        result = cur.execute("SELECT * FROM users WHERE username=%s", [username])
        #print(result)

        if result > 0:
            # Get the information to validate
            data = cur.fetchone()
            #print(data)
            password = data['password']

            # Comparing the passwords
            if sha256_crypt.verify(password_candidate, password):
                # Statred session and store the username into the session
                session['logged_in'] = True
                session['username'] = username
                #session['name'] = name

                flash('Welcome to the Technology Blog', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Incorrect Password, please try again'
                return render_template('login.html', error=error)

            # Close the DB connection
            cur.close()
        else:
            error = 'User not found'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Create a logout route
@app.route('/logout')
@is_logged_out
def logout():
    session.clear()
    flash('Bye, come back we are waiting', 'success')
    return redirect(url_for('login'))

# Create a dashboard route
@app.route('/dashboard')
@is_logged_out
def dashboard():

    # Create a cursor
    cur = mysql.connection.cursor()

    # Fetching the article
    result = cur.execute("SELECT * FROM articles")

    # Fetch all articles to display it on dashboard
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

    # Close the DB connection
    cur.close()

# Articles form
class ArticlesForm(Form):
    # Articles form field
    title = StringField('Title', [validators.DataRequired(), validators.Length(min=1, max=255)])
    body = TextAreaField('Body', [validators.DataRequired(), validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_out
def add_article():
    # Getting th form
    form = ArticlesForm(request.form)

    if request.method == 'POST' and form.validate():
            #If this is POST we need to grab the data from the user
            title = form.title.data
            body = form.body.data

            # Establish the DB connection
            cur = mysql.connection.cursor()

            # Fetching the Original name for the username
            # result = cur.execute("SELECT * from users WHERE username=%s",(session['username'])
            # if result > 0:
            #     data = cur.fetchone()
            #     name = data['name']

            # Inserting the values to the DB
            cur.execute("INSERT INTO articles(title, author, body) VALUES(%s, %s, %s)", (title, session['username'], body))

            # Commit to the DB
            mysql.connection.commit()

            # Close the DB
            cur.close()

            flash('Article created successfully','success')
            return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/delete_article/<string:id>/', methods=['POST'])
@is_logged_out
def delete_article(id):
    # Establishing a connection
    cur = mysql.connection.cursor()

    # Delete query
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    # Commiting
    mysql.connection.commit()

    # Close the connection
    cur.close()
    flash('Deleted the article successfully', 'success')
    return redirect(url_for('dashboard'))

# Start the application
if __name__ == '__main__':
    app.secret_key="appSimpleBlogTesting123"
    app.run(debug=True)
