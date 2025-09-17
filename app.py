from flask import Flask, request, jsonify, session
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS
import os




app = Flask(__name__)
UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(
    app, 
    supports_credentials=True,
    origins=['http://localhost:3001'])

app.secret_key = 'hudcfijefv4567'




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







@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    cursor.execute('SELECT * FROM users WHERE users_email=%s AND users_password=%s', (email, password))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user['users_id']
        return jsonify({"message": "Login exitoso", "user": user}), 200
    else:
        return jsonify({"message": "Credenciales incorrectas"}), 401
    







@app.route('/check_session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'user_id': session['user_id']})
    return jsonify({'logged_in': False})







@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'sesión cerrada'}), 200





@app.route('/create_news', methods=['POST'])
def create_news():
    if 'users_id' not in session:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    users_id = session['users_id']
    title = request.form['title']
    content = request.form['content']
    category = request.form['category']
    cover_image = None

    if 'cover' in request.files:
        file = request.files['cover']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        cover_image = f'/{filepath}'

    cursor = connection.cursor()
    cursor.execute("INSERT INTO news (news_users_id, news_title, news_content, news_category, news_cover_image) VALUES (%s, %s, %s, %s, %s)",
                   (users_id, title, content, category, cover_image))

    connection.commit()
    return jsonify({'msg': 'La nueva noticia ha sido creada'})






@app.route('/upload_news_image/<int:news_id>', methods=['POST'])
def upload_news_image(news_id):
    if 'users_id' not in session:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file'})
    
    file = request.files['file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    news_images = f'/{filepath}'

    cursor = connection.cursor()
    cursor.execute('INSERT INTO news_images (news_id, news_images) VALUES (%s, %s)', (news_id, news_images))
    connection.commit()
    return jsonify({'url': news_images})







@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'no selected file'})
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    image_url = f'/{filepath}'

    return jsonify({'url': image_url})




@app.route('/get_news', methods=['GET'])
def get_news():
    
    cursor.execute('SELECT n.news_id, n.news_title, n.news_content, n.news_cover_image, n.news_category, n.created_at, n.updated_at, u.users_name FROM news n JOIN users u ON n.news_users_id = u.users_id ORDER BY n.created_at DESC')

    news = cursor.fetchall()
    return jsonify(news)




@app.route('/get_news/<int:news_id>', methods=['GET'])
def get_news_item(news_id):
    
    cursor.execute('SELECT n.news_id, n.news_title, n.news_content, n.news_cover_image, n.news_category, n.created_at, n.updated_at, u.users_name FROM news n JOIN users u ON n.news_users_id = u.users_id WHERE n.news_id = %s', (news_id,))
    news_item = cursor.fetchone()

    if not news_item:
        return jsonify({'error': 'No encuentro la noticia que estás buscando'}), 404
    
    return jsonify(news_item)






@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get('users_name')
    email = data.get('users_email')
    password = data.get('users_password')

    if not name or not email or not password:
        return jsonify({"message": "Faltan datos"}), 400
    
    try:
        cursor.execute("INSERT INTO users (users_name, users_email, users_password) VALUES (%s, %s, %s)", (name, password, email))
        return jsonify({"message": "Usuario registrado con éxito"}), 201
    except mysql.connector.Error as err:
        return jsonify({"message": f"Error: {err}"}), 400


@app.route('/api/users', methods=['GET'])
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
    app.run(host='localhost', port=5005, debug=True)

@app.teardown_appcontext
def close_connection(exception):
    if connection.is_connected():
        cursor.close()
        connection.close()
        print('MySQL connection is closed')
