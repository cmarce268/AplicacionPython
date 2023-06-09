from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import bcrypt
import jwt
from datetime import datetime, timedelta
from bson import ObjectId


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ClaveUnica'
if __name__ == '__main__':
    app.run(port=8000)

# Configuración de la base de datos MongoDB
app.config['MONGO_DBNAME'] = 'mydatabase'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/mydatabase'

mongo = PyMongo(app)


# Registro de usuario
@app.route('/register', methods=['POST'])
def register():
    users = mongo.db.users
    existing_user = users.find_one({'username': request.json['username']})

    if existing_user:
        return jsonify({'message': 'User already exists.'}), 400

    hashed_password = bcrypt.hashpw(request.json['password'].encode('utf-8'), bcrypt.gensalt())

    user_id = users.insert({
        'username': request.json['username'],
        'password': hashed_password,
        'role': 'user'
    })

    token = jwt.encode({'user_id': str(user_id)}, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': token.decode('utf-8')}), 201


# Inicio de sesión de usuario
@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'username': request.json['username']})

    if login_user:
        if bcrypt.checkpw(request.json['password'].encode('utf-8'), login_user['password']):
            expiration_time = datetime.utcnow() + timedelta(minutes=30)
            token = jwt.encode({'user_id': str(login_user['_id']), 'exp': expiration_time},
                               app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({'token': token.decode('utf-8'), 'expiration_time': expiration_time}), 200

    return jsonify({'message': 'Invalid username/password combination.'}), 401


# Obtener todos los recursos
@app.route('/resources', methods=['GET'])
def get_resources():
    resources = mongo.db.resources.find()
    return jsonify({'resources': [r for r in resources]}), 200


# Obtener un recurso por ID
@app.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    resource = mongo.db.resources.find_one({'_id': ObjectId(resource_id)})
    if resource:
        return jsonify({'resource': resource}), 200
    else:
        return jsonify({'message': 'Resource not found.'}), 404


# Crear un nuevo recurso
@app.route('/resources', methods=['POST'])
def create_resource():
    if not request.json:
        return jsonify({'message': 'No data provided.'}), 400

    new_resource = {
        'name': request.json['name'],
        'description': request.json.get('description', ''),
        'category': request.json.get('category', ''),
        'owner_id': request.json.get('owner_id', ''),
        'created_at': datetime.utcnow()
    }

    resource_id = mongo.db.resources.insert(new_resource)
    resource = mongo.db.resources.find_one({'_id': resource_id})

    return jsonify({'resource': resource}), 201
# Actualizar un recurso existente
@app.route('/resources/<resource_id>', methods=['PUT'])
def update_resource(resource_id):
    try:
        # Obtener los datos del recurso a actualizar
        resource = mongo.db.resources.find_one({'_id': ObjectId(resource_id)})
        
        if not resource:
            return jsonify({'message': 'Resource not found.'}), 404
        
        # Obtener los datos a actualizar del cuerpo de la petición
        data = request.json

        # Actualizar los datos del recurso
        resource['name'] = data['name']
        resource['description'] = data['description']
        resource['category'] = data['category']
        mongo.db.resources.save(resource)

        # Crear la respuesta con el recurso actualizado
        response = jsonify({
            '_id': str(resource['_id']),
            'name': resource['name'],
            'description': resource['description'],
            'category': resource['category']
        })

        # Establecer el código de estado de la respuesta a 200 OK
        response.status_code = 200

        # Devolver la respuesta
        return response
    except Exception as e:
        # Si ocurre cualquier otra excepción, devolver una respuesta con código de estado 500 Internal Server Error
        response = jsonify({'error': str(e)})
        response.status_code = 500
        return response

