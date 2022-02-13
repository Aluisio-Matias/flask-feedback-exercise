
from flask import Flask, render_template, redirect, session
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, DeleteForm, FeedbackForm


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///users_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.debug = True
app.config["SECRET_KEY"] = "SecretApp123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

@app.route('/')
def homepage():
    return redirect('/register')

###############Error handling routes###############################

@app.errorhandler(404)
def page_not_found(e):
    '''Show 404 page not found'''
    return render_template('404.html'), 404

@app.errorhandler(401)
def not_allowed(e):
    '''Show the 401 page not authorized'''
    return render_template('401.html'), 401

####################################################################


################Users routes########################################

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''Register new user, display form and handle submission.'''

    if 'username' in session:
        return redirect(f'/users/{session["username"]}')

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email, first_name, last_name)

        db.session.commit()
        session['username'] = user.username

        return redirect(f'/users/{user.username}')

    else:
        return render_template('users/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Display the login form and handle submission.'''

    if 'username' in session:
        return redirect(f'/users/{session["username"]}')

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password.']
            return render_template('users/login.html', form=form)

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    '''Handle logout'''

    session.pop('username')
    return redirect('/login')


@app.route('/users/<username>')
def show_user(username):
    '''Page for logged in users.'''

    if 'username' not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    form = DeleteForm()

    return render_template('users/show.html', user=user, form=form)


@app.route('/users/<username>/delete', methods=['POST'])
def remove_user(username):
    '''Delete user then redirect to Login page'''

    if 'username' not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop('username')

    return redirect('/login')


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    """Display the add-feedback form and handle it."""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            username=username,
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    else:
        return render_template("feedback/new.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("/feedback/edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")