# Flask Imports
from flask import Flask, request, redirect, url_for, render_template, jsonify, flash, make_response
from flask import session as login_session
from flask import jsonify
# Database Imports
from database_setup import Base, User, Item, Category
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
# Utility Imports
import json
import random
import string
import httplib2
# Oauth2 
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

# Database connection
engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False})

Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()


# Oauth credentials
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# Flask Initialization
app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(10).all()
    return render_template('index.html', categories=categories, items=items)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        userExsists = session.query(User).filter_by(username=username).first()

        # checking Username is unique
        if userExsists is not None:
            response = make_response(json.dumps(
                'Current username taken.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        userExsists = session.query(User).filter_by(email=email).first()

        # Checking email is unique
        if userExsists is not None:
            response = make_response(json.dumps('Current email taken.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Checking passwords confirmation
        if request.form['password'] != request.form['verifyPassword']:
            response = make_response(json.dumps(
                'Password verificaiton failed. Passwords must match'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        newUser = User(username=username, email=email)
        newUser.hash_password(request.form['password'])

        session.add(newUser)
        session.commit()

        flash("You are registered! Login now.")

        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html')

    if request.method == 'POST':
        user = session.query(User).filter_by(
            username=request.form['username']).first()

        # Checking if user is in DB
        if user is None:
            response = make_response(json.dumps(
                'Username and Password combination invalid.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Checking Password. If right, setting session
        if user.verify_password(request.form['password']):
            login_session['user_id'] = user.id
            flash('You are logged in as user %s' % user.id)
            return redirect(url_for('index'))
        else:
            response = make_response(json.dumps(
                'Username and Password combination invalid.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response


@app.route('/logout', methods=['GET'])
def logout():
    # Checking if session exists
    if 'user_id' not in login_session:
        return redirect(request.referrer)

    del login_session['user_id']
    flash('You are logged out!')
    return redirect(request.referrer)


@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate the State Token
    if 'state' not in login_session:
        flash('State token incorrect. Please try again.')
        return redirect(url_for('index'))

    code = request.data



    return 'Blah'



@app.route('/catalog/items/new', methods=['GET', 'POST'])
def createItem():
    if request.method == 'GET':
        # Checking if session exists
        if 'user_id' not in login_session:
            return redirect(url_for('login'))

        categories = session.query(Category).all()
        return render_template('newitem.html', categories=categories)

    if request.method == 'POST':
        # Checking if session exists.
        try:
            user_id = login_session['user_id']
        except:
            response = make_response(json.dumps('Not Authorized.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        title = request.form['title']
        description = request.form['description']
        category = request.form['category']

        # Checking all fields are filled out
        if category or description or category is None:
            flash('Not all fields were completed. Please try again.')
            return redirect(url_for('createItem'))

        testQuery = session.query(Item).filter_by(title=title).first()
        # Making sure Item does not exist already.
        if testQuery is not None:
            flash('Item already exists. Please try again.')
            return redirect(url_for('createItem'))

        # Tests passed. Creating Item.
        categoryObject = session.query(
            Category).filter_by(name=category).first()
        newItem = Item(title=title, description=description,
                       category_id=categoryObject.id, user_id=user_id)
        session.add(newItem)
        session.commit()
        flash('%s item created!' % newItem.title)
        return redirect(url_for('index'))


@app.route('/catalog/<catName>/<itemName>/edit', methods=['GET', 'POST'])
def editItem(catName, itemName):
    if request.method == 'GET':

        # Checking active session.
        try:
            user_id = login_session['user_id']
        except:
            return redirect(url_for('login'))

        item = session.query(Item).filter_by(title=itemName).first()

        # Checking User Perms
        if user_id != item.user_id:
            flash('Sorry. You do not have permission to edit.')
            return redirect(request.referrer)

        cat = session.query(Category).filter_by(name=catName).first()
        categories = session.query(Category).all()

        # Validating route
        if cat == None or item == None:
            flash('Sorry, item not found.')
            return redirect(request.referrer)
        if cat.id != item.category_id:
            flash('Sorry, item not found.')
            return redirect(request.referrer)

        return render_template('edititem.html', item=item, categories=categories)

    if request.method == 'POST':
        newTitle = request.form['title']
        newDescription = request.form['description']
        newCatName = request.form['category']
        item = session.query(Item).filter_by(title=itemName).first()
        # Checking active session
        try:
            user_id = login_session['user_id']
        except:
            return redirect(url_for('login'))

        # Validating User Permissions
        if item.user_id != user_id:
            response = make_response(json.dumps(
                'User not authorized to edit.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        if newTitle == '':
            flash('Edit failed. A title must be entered.')
            return redirect(request.referrer)

        if newCatName == '':
            response = make_response(json.dumps(
                'Category must be chosen.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Editing Item in DB
        newCat = session.query(Category).filter_by(name=newCatName).first()
        item.title = newTitle
        item.description = newDescription
        item.cat = newCat

        session.add(item)
        session.commit()
        flash('Item %s edited' % item.title)
        return redirect(url_for('index'))


@app.route('/catalog/<catName>/<itemName>/delete', methods=['GET', 'POST'])
def deleteItem(catName, itemName):
    if request.method == 'GET':
        queryitem = session.query(Item).filter_by(title=itemName).first()
        # Checking existing session
        try:
            user_id = login_session['user_id']
        except:
            return redirect(url_for('login'))

        # Checking Route
        if queryitem == None:
            flash('Sorry, page not found.')
            return redirect(request.referrer)

        # Validating route
        if queryitem.category.name != catName:
            flash('Sorry, page not found.')
            return redirect(request.referrer)

        # Checking User Permissions
        if user_id != queryitem.user_id:
            flash('User not authorized access.')
            return redirect(request.referrer)

        return render_template('deleteitem.html', item=queryitem)

    if request.method == 'POST':
        item = session.query(Item).filter_by(id=request.form['itemID']).first()

        # Checking active session
        try:
            user_id = login_session['user_id']
        except:
            response = make_response(json.dumps(
                'User not authorized access.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Checking if query returned item
        if item == None:
            response = make_response(json.dumps('Item not found.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Validating user permissions
        if item.user_id != user_id:
            response = make_response(json.dumps(
                'User not authorized access.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        session.delete(item)
        session.commit()
        flash('%s item deleted.' % item.title)
        return redirect(url_for('index'))


@app.route('/catalog/categories/new', methods=['GET', 'POST'])
def createCategory():
    if request.method == 'GET':
        # Checking active session
        try:
            user_id = login_session['user_id']
        except:
            flash('Please login first.')
            return redirect(url_for('login'))

        return render_template('newcategory.html')

    if request.method == 'POST':
        name = request.form['name']

        # Checking active session
        try:
            user_id = login_session['user_id']
        except:
            response = make_response(json.dumps('Must be logged in.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Checking input
        if name is None:
            flash('Please complete all fields.')
            return redirect(request.referrer)

        # Creating Category
        newCategory = Category(name=name, user_id=user_id)
        session.add(newCategory)
        session.commit()
        flash("%s category created." % newCategory.name)

        return redirect(url_for('index'))


@app.route('/catalog/<category>/edit', methods=['GET', 'POST'])
def editCategory(category):
    if request.method == 'GET':

        # Checking active session
        try:
            user_id = login_session['user_id']
        except:
            return redirect(url_for('login'))

        oldCategory = session.query(Category).filter_by(name=category).first()

        # Validating user permissions
        if user_id != oldCategory.user_id:
            flash('User is not authorized to edit.')
            return redirect(request.referrer)

        return render_template('editcategory.html', category=oldCategory)

    if request.method == 'POST':
        newName = request.form['newName']

        # Checking active session
        try:
            user_id = login_session['user_id']
        except:
            response = make_response(json.dumps('Must be logged in.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Checking input exists
        if newName is None:
            flash('All form fields must be filled out. Please try again')
            return redirect(request.referrer)

        test = session.query(Category).filter_by(name=newName).first()

        # Checks to see if category already exists
        if test is not None:
            flash('Category name already exists. Please try again.')
            return redirect(request.referrer)

        oldCategory = session.query(Category).filter_by(name=category).first()

        # Validating user permissions
        if oldCategory.user_id != user_id:
            response = make_response(json.dumps(
                'User not authorized access.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Editing Category

        oldCategory.name = newName
        session.add(oldCategory)
        session.commit()
        flash('%s category changed to: %s' % (category, newName))

        return redirect(url_for('index'))


@app.route('/catalog/<name>', methods=['GET'])
def getItemsFromCategory(name):
    thecategory = session.query(Category).filter_by(name=name).first()
    items = session.query(Item).filter_by(category_id=thecategory.id).all()
    return render_template('categoryitems.html', items=items, category=thecategory)


@app.route('/catalog/<name>/<title>', methods=['GET'])
def getItem(name, title):
    if request.method == 'GET':
        thecategory = session.query(Category).filter_by(name=name).first()
        item = session.query(Item).filter_by(title=title).first()
        if item.category_id != thecategory.id:
            flash('Sorry, page item not found.')
            return redirect(request.referrer)

        return render_template('item.html', item=item)


@app.route('/api/json', methods=['GET'])
def json_api():
    """Returns a JSON object of all items orginized by category."""
    items = session.query(Item).all()
    categories = session.query(Category).all()

    # Establishing Dict
    cat_item = {'category': []}

    # Assigning out items to category
    i = 0
    for category in categories:
        cat_item['category'].append(category.serialize)
        cat_item['category'][i]['items'] = []
        for item in items:
            if category.id == item.category_id:
                cat_item['category'][i]['items'].append(item.serialize)
        i += 1

    return jsonify(cat_item)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'ASDhshhWj1654g651j51cvxs5d61as6d5'
    app.run(host='0.0.0.0', port=5000)
