from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect, generate_csrf
from config import config
from flask_login import LoginManager, login_user, logout_user, login_required

from models.ModelUser import ModelUser
from models.entities.User import User


app = Flask(__name__)

db = MySQL(app)
login_manager_app = LoginManager(app)
csrf = CSRFProtect()

# Esta función permite usar {{ csrf_token() }} en cualquier plantilla
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['username'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                flash("Invalid password...")
                return render_template('auth/login.html')
        else:
            flash("Usuario no existe...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    cur = db.connection.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    cur.close()
    return render_template('home.html', productos=data)

@app.route('/add', methods=['POST'])
def add_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']
        cur = db.connection.cursor()
        cur.execute("INSERT INTO productos (nombre, precio, stock) VALUES (%s,%s,%s)", (nombre, precio, stock))
        db.connection.commit()
        cur.close
        return redirect(url_for('home'))
    
@app.route('/edit/<int:id>', methods=['POST', 'GET'])
def edit_producto(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        stock = request.form['stock']
        cur = db.connection.cursor()
        cur.execute("UPDATE productos SET nombre=%s, precio=%s, stock=%s WHERE id=%s", (nombre, precio, stock, id))
        db.connection.commit()
        cur.close
        return redirect(url_for('home'))
    else:
        cur = db.connection.cursor()
        cur.execute('SELECT * FROM productos WHERE id = %s', (id,))
        data = cur.fetchone()
        cur.close()
        return render_template('edit.html', producto=data)
    
@app.route('/delete/<int:id>')
def delete_producto(id):
    cur = db.connection.cursor()
    cur.execute('DELETE FROM productos WHERE id = %s', (id,))
    db.connection.commit()
    cur.close()
    return redirect(url_for('home'))

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

if __name__ =='__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run()

