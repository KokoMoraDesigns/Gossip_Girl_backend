from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS

app = Flask(__name__)
CORS(app)




def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(

            host='localhost',
            user='root',
            password='16abril2012',
            database='Gossip_Girl_Content'
        )

        if connection.is_connected():
            print('Connected to MySQL')
    
    except Error as e:
        print(f'Error: {e}')
    
    return connection



connection = create_connection()
cursor = connection.cursor(dictionary=True)

@app.route('/')
def hello_world():
    return 'Te amo, mi Amatxito maravillosísima'

@app.route('/users', methods=['GET'])
def get_users():
    try:
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        return jsonify(users)
    
    except Error as e:
        return jsonify({'error': str(e)})


@app.route('/users', methods=['POST'])
def add_user():
    try:
        user = request.json
        cursor.execute('INSERT INTO users (name, password) VALUES (%s, %s)', (user['name'], user['password']))
        connection.commit()
        return jsonify({'id': cursor.lastrowid})
    except Error as e:
        return jsonify({'error': str(e)})

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    try:
        user = request.json
        cursor.execute('UPDATE users SET name = %s, password = %s WHERE id = %s', (user['name'], user['password'], id))
        connection.commit()
        return 'User updated'
    except Error as e:
        return jsonify({'error': str(e)})
    
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        cursor.execute('DELETE FROM users WHERE id = %s', (id,))
        connection.commit()
        return 'User deleted'
    except Error as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(port=5005, debug=True)

@app.teardown_appcontext
def close_connection(exception):
    if connection.is_connected():
        cursor.close()
        connection.close()
        print('MySQL connection is closed')