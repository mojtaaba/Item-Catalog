from flask import Flask, render_template, url_for, request, redirect, jsonify, make_response, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session
import random, string, json, httplib2, requests
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///Catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    DBSession = sessionmaker(bind=engine)
    sessions = DBSession()
    sessions.add(newUser)
    sessions.commit()
    user = sessions.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    DBSession = sessionmaker(bind=engine)
    sessions = DBSession()
    user = sessions.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        DBSession = sessionmaker(bind=engine)
        sessions = DBSession()
        user = sessions.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/')
@app.route('/catalog')
def showCategories():
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	categories = sessions.query(Category).all()
	categoryItems = sessions.query(CategoryItem).all()
	return render_template('MainMenu.html', categories = categories, categoryItems = categoryItems)

@app.route('/catalog/<int:catalog_id>')
@app.route('/catalog/<int:catalog_id>/items')
def showCategory(catalog_id):
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	categories = sessions.query(Category).all()

	category = sessions.query(Category).filter_by(id = catalog_id).first()

	categoryName = category.name

	categoryItems = sessions.query(CategoryItem).filter_by(category_id = catalog_id).all()

	categoryItemsCount = sessions.query(CategoryItem).filter_by(category_id = catalog_id).count()

	return render_template('category.html', categories = categories, categoryItems = categoryItems, categoryName = categoryName, categoryItemsCount = categoryItemsCount)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>')
def showCategoryItem(catalog_id, item_id):
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	categoryItem = sessions.query(CategoryItem).filter_by(id = item_id).first()

	creator = getUserInfo(categoryItem.user_id)

	return render_template('Item.html', categoryItem = categoryItem, creator = creator)

@app.route('/catalog/add', methods=['GET', 'POST'])
def addItem():
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	if 'username' not in login_session:
	    return redirect('/login')

	if request.method == 'POST':

		if not request.form['name']:
			flash('Please add item name')
			return redirect(url_for('addItem'))

		if not request.form['description']:
			flash('Please add a description')
			return redirect(url_for('addItem'))

		newCategoryItem = CategoryItem(name = request.form['name'], description = request.form['description'], category_id = request.form['category'], user_id = login_session['user_id'])
		sessions.add(newCategoryItem)
		sessions.commit()
		flash('Movie  Successfully added')
		return redirect(url_for('showCategories'))
	else:

		categories = sessions.query(Category).all()

		return render_template('addItem.html', categories = categories)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(catalog_id, item_id):
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()

	if 'username' not in login_session:
	    return redirect('/login')


	categoryItem = sessions.query(CategoryItem).filter_by(id = item_id).first()


	creator = getUserInfo(categoryItem.user_id)


	if creator.id != login_session['user_id']:
		return redirect('/login')


	categories = sessions.query(Category).all()

	if request.method == 'POST':
            if request.form['name']:
    			categoryItem.name = request.form['name']
            if request.form['description']:
    			categoryItem.description = request.form['description']
            if request.form['category']:
    			categoryItem.category_id = request.form['category']
            sessions.add(categoryItem)
            sessions.commit()
            flash('Movie Successfully Edited')
            return redirect(url_for('showCategoryItem', catalog_id = categoryItem.category_id ,item_id = categoryItem.id))
        else:
		    return render_template('editItem.html', categories = categories, categoryItem = categoryItem)

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(catalog_id, item_id):
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()

	if 'username' not in login_session:
	    return redirect('/login')


	categoryItem = sessions.query(CategoryItem).filter_by(id = item_id).first()


	creator = getUserInfo(categoryItem.user_id)


	if creator.id != login_session['user_id']:
		return redirect('/login')

	if request.method == 'POST':
		sessions.delete(categoryItem)
		sessions.commit()
		flash('Movie Successfully deleted')
		return redirect(url_for('showCategory', catalog_id = categoryItem.category_id))
	else:
		return render_template('deleteItem.html', categoryItem = categoryItem)

@app.route('/login')
def login():

	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state

	return render_template('login.html', STATE=state)

@app.route('/logout')
def logout():
	if login_session['provider'] == 'facebook':
		fbdisconnect()
		del login_session['facebook_id']

	if login_session['provider'] == 'google':
		gdisconnect()
		del login_session['gplus_id']
		del login_session['access_token']

	del login_session['username']
	del login_session['email']
	del login_session['picture']
	del login_session['user_id']
	del login_session['provider']

	return redirect(url_for('showCategories'))


@app.route('/fbconnect', methods=['POST'])
def fbconnect():

	if request.args.get('state') != login_session['state']:
	    response = make_response(json.dumps('Invalid state parameter.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response


	access_token = request.data
	print "access token received %s " % access_token


	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']

	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]


	userinfo_url = "https://graph.facebook.com/v2.4/me"


	token = result.split("&")[0]

	url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data["name"]
	login_session['email'] = data["email"]
	login_session['facebook_id'] = data["id"]


	stored_token = token.split("=")[1]
	login_session['access_token'] = stored_token


	url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data["data"]["url"]


	user_id = getUserID(login_session['email'])
	if not user_id:
	    user_id = createUser(login_session)
	login_session['user_id'] = user_id

	return "Login Successful!"

@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	access_token = login_session['access_token']

	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]

	return "you have been logged out"

@app.route('/gconnect', methods=['POST'])
def gconnect():

	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response


	code = request.data

	try:

		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response


	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])


	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response


	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response


	if result['issued_to'] != CLIENT_ID:
		response = make_response(json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_access_token = login_session.get('access_token')
	stored_gplus_id = login_session.get('gplus_id')

	if stored_access_token is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response


	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id


	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	login_session['provider'] = 'google'


	user_id = getUserID(data["email"])
	if not user_id:
	    user_id = createUser(login_session)
	login_session['user_id'] = user_id

	return "Login Successful"

@app.route('/gdisconnect')
def gdisconnect():

	access_token = login_session.get('access_token')

	if access_token is None:
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	if result['status'] != '200':

	    response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
	    response.headers['Content-Type'] = 'application/json'
	    return response

@app.route('/catalog/JSON')
def showCategoriesJSON():
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	categories = sessions.query(Category).all()
	return jsonify(categories = [category.serialize for category in categories])

@app.route('/catalog/<int:catalog_id>/JSON')
@app.route('/catalog/<int:catalog_id>/items/JSON')
def showCategoryJSON(catalog_id):
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	categoryItems = sessions.query(CategoryItem).filter_by(category_id = catalog_id).all()
	return jsonify(categoryItems = [categoryItem.serialize for categoryItem in categoryItems])

@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/JSON')
def showCategoryItemJSON(catalog_id, item_id):
	DBSession = sessionmaker(bind=engine)
	sessions = DBSession()
	categoryItem = sessions.query(CategoryItem).filter_by(id = item_id).first()
	return jsonify(categoryItem = [categoryItem.serialize])

if __name__ == '__main__':
	app.debug = True
	app.secret_key = 'super_secret_key'
	app.run(host = '0.0.0.0', port = 8000)
