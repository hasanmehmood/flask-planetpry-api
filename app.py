import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float

from flask_marshmallow import Marshmallow
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, jwt_required, create_access_token



app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret' # something very diff for prod!
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


# ------------ CLI commands 
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Datebase Created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Datebase Dropped!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=2.258e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                         planet_type='Class K',
                         home_star='Sol',
                         mass=4.867e24,
                         radius=3760,
                         distance=67.24e6)

    earth = Planet(planet_name='Earth',
                     planet_type='Class M',
                     home_star='Sol',
                     mass=5.972e24,
                     radius=3959,
                     distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='hassan',
                     last_name='mehmood',
                     email='hassan@testemail.commands',
                     password='p@ssw0rd')

    db.session.add(test_user)
    db.session.commit()
    print('Datebase Seeded!')


# ------------ API endpoints
@app.route('/')
def hello_world():
    return 'Hello, World!!!!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='This is my super simple', success=True), 200


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 14: 
        return jsonify(message='Sorry! You are not old enough!'), 401
    return jsonify(message=f'Welcome {name}! You are old enough'), 200


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 14: 
        return jsonify(message='Sorry! You are not old enough!'), 401
    return jsonify(message=f'Welcome {name}! You are old enough'), 200


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='The email already exists.'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email,
            password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='User created successfully.'), 201


@app.route('/login', methods=['POST'])
def login():
    
    # Check if received data is in json form
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login Succeeded.', access_token=access_token)
    else:
        return jsonify(message='You entered a bad email or password'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message(f'Your Planetory password is {user.password}',
            sender='no-reply@planetorapi.com', recipients=[email])
        mail.send(msg)
        return jsonify(message=f'Password sent to {email}')
    return jsonify(message='That email does not exist.')


@app.route('/planet_details/<string:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    return jsonify(message=f'Planet with ID: {planet_id} does not exist.'), 404


@app.route('/add_planet', methods=['POST'])
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message='Planet already exist.'), 409

    planet_type = request.form['planet_type']
    home_star = request.form['home_star']
    mass = float(request.form['mass'])
    radius = float(request.form['radius'])
    distance = float(request.form['distance'])

    planet = Planet(planet_name=planet_name, planet_type=planet_type,
        home_star=home_star, mass=mass, radius=radius, distance=distance)
    db.session.add(planet)
    db.session.commit()

    return jsonify(message=f'Planet "{planet_name}" added successfully.')


# Models
class User(db.Model):

    # Control name of table when created by sqlchemy
    __tablename__ = 'users'

    # columns for the table users
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):

    __tablename__ = 'planets'

    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 
            'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run()
