from flask import Flask, request, jsonify, session
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import json




app = Flask(__name__)
CORS(
    app, 
    supports_credentials=True,
    origins=['http://localhost:3001']
)



UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1) [1].lower() in ALLOWED_EXTENSIONS



app.secret_key = 'hudcfijefv4567'
app.config['SESSION_COOKIE_SAMESITE'] = None
app.config['SESSION_COOKIE_SECURE'] = False




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
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    cursor.execute('SELECT * FROM users WHERE users_email=%s AND users_password=%s', (email, password))
    user = cursor.fetchone()

    if user:
        session['logged_in'] = True
        session['email'] = user['users_email']
        session['user_id'] = user['users_id']
        return jsonify({
            'logged_in': True,
            'user': {
                'id': user['users_id'],
                'email': user['users_email'],
                'name': user['users_name']
            },
            "message": "Login exitoso"
        }), 200
            
    else:
        return jsonify({
            'logged_in': False,
            'user': None,
            "message": "Credenciales incorrectas"
        }), 401
    







@app.route('/check_session', methods=['GET'])
def check_session():
    print('DEBUG session:', dict(session))
    if session.get('logged_in'):
        return jsonify({
            'logged_in': True, 
            'email': session.get('email'),
            'user_id': session.get('user_id')
        }), 200
    return jsonify({
        'logged_in': False,
        'email': None,
        'user_id': None
    }), 200







@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({
        'logged_in': False,
        'message': 'sesión cerrada'
    }), 200






@app.route('/get_news', methods=['GET'])
def get_news():

    try:

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                news_id AS id,
                news_title AS title,
                news_content AS content,
                news_cover_image AS cover_image,
                news_category AS category,
                news_users_id AS user_id,
                news_images,
                created_at,
                updated_at
            FROM news
            ORDER BY news_id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        for row in rows:
            if row['news_images']:
                try:
                    row['news_images'] = json.loads(row['news_images'])
                except:
                    row['news_images'] = []
            else:
                row['news_images'] = []


        return jsonify({'newspaper_items': rows})
    
    except Exception as e:
        print('error in get_news:', e)
        return jsonify({'error': str(e)}), 500



@app.route('/get_news/<category>', methods=['GET'])
def get_news_by_category(category):
    try:

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
    
        query = """
            SELECT 
                news_id AS id,
                news_title AS title,
                news_content AS content,
                news_cover_image AS cover_image,
                news_category AS category,
                news_users_id AS user_id,
                news_images,
                created_at,
                updated_at
            FROM news
            WHERE news_category = %s
            ORDER BY news_id DESC
        """
        cursor.execute(query, (category,))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        for row in rows:
            if row['news_images']:
                try:
                    row['news_images'] = json.loads(row['news_images'])
                except:
                    row['news_images'] = []
            else:
                row['news_images'] = []        

        return jsonify({'newspaper_items': rows})
    
    except Exception as e:
        print('error in get_news_by_category:', e)
        return jsonify({'error': str(e)}), 500





@app.route('/get_news/<int:news_id>', methods=['GET'])
def get_news_item(news_id):

    try: 
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
    
        query = 'SELECT n.news_id AS id, n.news_title AS title, n.news_content AS content, n.news_cover_image AS cover_image, n.news_category AS category, n.created_at AS created_at, n.updated_at AS updated_at, n.news_images, u.users_name AS author FROM news n JOIN users u ON n.news_users_id = u.users_id WHERE n.news_id = %s'
        cursor.execute(query, (news_id,))
        news_item = cursor.fetchone()

        cursor.close()
        connection.close()

        if not news_item:
            return jsonify({'error': 'No encuentro la noticia que estás buscando'}), 404
        
        if news_item['news_images']:
            try:
                news_item['news_images'] = json.loads(news_item['news_images'])
                
            except:
                news_item['news_images'] = []
        else:
            news_item['news_images'] = []
        
        return jsonify(news_item)
        
    
    except Exception as e:
        print('error in get_news_item:', e)
        return jsonify({'error': str(e)}), 500



@app.route('/add_news', methods=['POST'])
def add_news():
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        user_id = request.form.get('user_id')


        cover_image_url = None

        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                cover_image_url = f'/static/images/{filename}'



            
        extra_images = []
        if 'news_images' in request.files:
            files = request.files.getlist('news_images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    extra_images.append(f'/static/images/{filename}')

        images_str = json.dumps(extra_images) if extra_images else None

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = '''

            INSERT INTO news (news_title, news_content, news_cover_image, news_category, news_users_id, news_images, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        '''

        cursor.execute(query, (title, content, cover_image_url, category, user_id, images_str))
        connection.commit()

        new_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return jsonify({'message': 'la noticia ha sido creada con éxito', 'id': new_id }), 201
    
    except Exception as e:
        print('error in add_new:', e)
        return jsonify({'error': str(e)}), 500
    


@app.route('/update_news/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    try:

        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')

        cover_image_url = None
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                cover_image_url = f'/static/images/{filename}'


        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT news_images FROM news WHERE news_id = %s', (news_id,))
        row = cursor.fetchone()

        existing_images = []
        if row and row['news_images']:
            try:
                existing_images = json.loads(row['news_images'])
            except:
                existing_images = []


        new_images = []
        if 'news_images' in request.files:
            files = request.files.getlist('news_images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    new_images.append(f'/static/images/{filename}')

        all_images = existing_images + new_images
        images_str = json.dumps(all_images) if all_images else None



        query = '''
            UPDATE news
            SET news_title = %s,
                news_content = %s,
                news_category = %s,
                updated_at = NOW()
            WHERE news_id = %s
        '''

        cursor.execute(query, (title, content, category, news_id))

        if cover_image_url:
            cursor.execute(
                'UPDATE news SET news_cover_image = %s WHERE news_id = %s', (cover_image_url, news_id)
            )

        
        cursor.execute('UPDATE news SET news_images = %s WHERE news_id = %s', (images_str, news_id))
        
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'la noticia se ha actualizado exitosamente'}), 200
    
    except Exception as e:
        print('error in update_news:', e)
        return jsonify({'error': str(e)}), 500
    


@app.route('/delete_news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = 'DELETE FROM news WHERE news_id = %s'
        cursor.execute(query, (news_id,))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'la noticia se ha eliminado con éxito'}), 200
    except Exception as e:
        print('error in delete_news:', e)
        return jsonify({'error': str(e)}), 500
    

    
@app.route('/delete_news_image/<int:news_id>', methods=['DELETE'])
def delete_news_image(news_id):
    try:
        data = request.json
        image_url = data.get('image_url')

        if not image_url:
            return jsonify({'error': 'no image url has been provided'}), 400
        
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute('SELECT news_images FROM news WHERE news_id = %s', (news_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'no encuentro la noticia que estás buscando'}), 404
        
        images = []
        if row['news_images']:
            try:
                images = json.loads(row['news_images'])
            except:
                images = []

        if image_url in images:
            images.remove(image_url)

        images_str = json.dumps(images) if images else None

        cursor.execute('UPDATE news SET news_images = %s WHERE news_id = %s', (images_str, news_id))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'message': 'Esta imagen ha sido eliminadacon éxito'}), 200
    
    except Exception as e:
        print('error in delete_news_image:', e)
        return jsonify({'error': str(e)}), 500
    















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
