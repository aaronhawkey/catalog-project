# Flask Imports
from flask import Flask, request, redirect, url_for, render_template, jsonify, flash, make_response
from flask import session as login_session
# Database Imports
from database_setup import Base, User, Item, Category
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
# Utility Imports
import json
import random, string

engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})

Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()



app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    categories = session.query(Category).all()
    return render_template('index.html', categories = categories)


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        userExsists = session.query(User).filter_by(username=username).first()


        #checking Username is unique
        if userExsists is not None:
            response = make_response(json.dumps('Current username taken.'), 409)
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
            response = make_response(json.dumps('Password verificaiton failed. Passwords must match'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response


        newUser = User(username = username, email = email)
        newUser.hash_password(request.form['password'])

        session.add(newUser)
        session.commit()

        flash("You are registered! Login now.")

        return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        user = session.query(User).filter_by(username = request.form['username']).first()
        
        if user is None:
            response = make_response(json.dumps('Username and Password combination invalid.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response

        if user.verify_password(request.form['password']):
            login_session['user_id'] = user.id
            flash('You are logged in as user %s' % user.id )
            return redirect(url_for('index'))
        else:
            response = make_response(json.dumps('Username and Password combination invalid.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response


@app.route('/logout', methods=['GET'])
def logout():
    try:
        id = login_session['user_id']
    except:
        return redirect(url_for('index'))
    
    del login_session['user_id']
    flash('You are logged out!')
    return redirect(url_for('index'))


@app.route('/catalog/items/new', methods=['GET', 'POST'])
def createItem():
    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('newitem.html', categories = categories)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        print title
        print description
        print category
        if (category or description or category) is None:
            response = make_response(json.dumps('Not all fields were filled out.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response
        categoryObject = session.query(Category).filter_by(name=category).first()
        newItem = Item(title = title, description = description, category_id = categoryObject.id)
        session.add(newItem)
        session.commit()
        flash('%s item created!' % newItem.title)
        return redirect(url_for('index'))


@app.route('/catalog/categories/new', methods=['GET', 'POST'])
def createCategory():
    if request.method == 'GET':
        return render_template('newcategory.html')
    if request.method == 'POST':
        name = request.form['name']
        if name is None:
            response = make_response(json.dumps('Not all fields were filled out.'), 409)
            response.headers['Content-Type'] = 'application/json'
            return response
        newCategory = Category(name = name)
        session.add(newCategory)
        session.commit()
        flash("%s category created." % newCategory.name)
        return redirect(url_for('index'))


@app.route('/catalog/<name>', methods=['GET'])
def getItemsFromCategory(name):
    thecategory = session.query(Category).filter_by(name= name).first()
    items = session.query(Item).filter_by(category_id = thecategory.id).all()
    return render_template('categoryitems.html', items = items, category = thecategory)


@app.route('/catalog/<name>/<title>', methods=['GET'])
def getItem(name, title):
    if request.method == 'GET':
        thecategory = session.query(Category).filter_by(name= name).first()
        item = session.query(Item).filter_by(title = title).first()
        if item.category_id != thecategory.id:
            response = make_response(json.dumps('Page not found'), 404)
            response.headers['Content-Type'] = 'application/json'
            return response
        
        return render_template('item.html', item = item)



if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'ASDhshhWj1654g651j51cvxs5d61as6d5'
    app.run(host='0.0.0.0', port=5000)