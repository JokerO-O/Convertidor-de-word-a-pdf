from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from docx import Document
import pdfkit
import os

# Crear la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Cambia esto a una clave secreta adecuada
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Crear la carpeta 'static' si no existe
if not os.path.exists('static'):
    os.makedirs('static')

# Define el modelo User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        new_user = User(username=username, password=password)

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('upload'))

        flash('Invalid credentials!')

    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.docx'):
            # Guardar el archivo temporalmente
            temp_doc_path = os.path.join('static', file.filename)
            file.save(temp_doc_path)

            # Verifica si el archivo se ha guardado correctamente
            if not os.path.exists(temp_doc_path):
                flash('File was not saved correctly.')
                return redirect(url_for('upload'))

            # Convertir el archivo Word a PDF
            pdf_filename = file.filename.replace('.docx', '.pdf')
            pdf_file_path = os.path.join('static', pdf_filename)

            try:
                # Leer el documento y crear un archivo PDF
                doc = Document(temp_doc_path)
                pdf_content = "\n".join(para.text for para in doc.paragraphs)

                # Usar pdfkit para convertir texto a PDF
                pdfkit.from_string(pdf_content, pdf_file_path)

                print(f'PDF creado correctamente: {pdf_file_path}')  # Mensaje de éxito
                # Eliminar el archivo temporal
                os.remove(temp_doc_path)

                return f'File converted successfully: <a href="{pdf_file_path}">Download PDF</a>'
            except Exception as e:
                print(f'Error al convertir el archivo: {str(e)}')  # Mensaje de error
                flash(f'Error al convertir el archivo: {str(e)}')
                return redirect(url_for('upload'))
        else:
            flash('Only .docx files are allowed!')

    return render_template('upload.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear todas las tablas una vez
    app.run(debug=True)
