from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.config['SECRET_KEY'] = 'handtohand_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banque.db'
db = SQLAlchemy(app)

# --- MODELES ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user') # user ou admin

class Compte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    numero_compte = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False) # depot, retrait, transfert
    montant = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    compte_id = db.Column(db.Integer, db.ForeignKey('compte.id'), nullable=False)
    compte_dest_id = db.Column(db.Integer, db.ForeignKey('compte.id'), nullable=True)
    description = db.Column(db.String(200))

# --- FONCTIONS UTILES ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return "Accès refusé", 403
        return f(*args, **kwargs)
    return decorated

def calculer_solde(compte_id):
    depots = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='depot').scalar() or 0
    retraits = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='retrait').scalar() or 0
    transferts_out = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='transfert').scalar() or 0
    transferts_in = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_dest_id=compte_id, type='transfert').scalar() or 0
    return depots - retraits - transferts_out + transferts_in

# --- ROUTES AUTH ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('accueil'))
        flash('Login ou mot de passe incorrect')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'])
        new_user = User(username=request.form['username'], password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash('Compte créé! Connectez-vous.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROUTES PRINCIPALES ---
@app.route('/accueil')
@login_required
def accueil():
    comptes = Compte.query.filter_by(user_id=session['user_id']).all()
    solde_total = sum([calculer_solde(c.id) for c in comptes])
    return render_template('accueil.html', comptes=comptes, solde_total=solde_total, calculer_solde=calculer_solde) 
# <-- AJOUTE calculer_solde ICI
@app.route('/creer_compte', methods=['GET', 'POST'])
@login_required
def creer_compte():
    if request.method == 'POST':
        import random
        num = 'HHM' + str(random.randint(100000, 999))
        compte = Compte(nom=request.form['nom'], numero_compte=num, user_id=session['user_id'])
        db.session.add(compte)
        db.session.commit()
        return redirect(url_for('accueil'))
    return render_template('creer_compte.html')

@app.route('/depot/<int:compte_id>', methods=['GET', 'POST'])
@login_required
def depot(compte_id):
    if request.method == 'POST':
        montant = float(request.form['montant'])
        trans = Transaction(type='depot', montant=montant, compte_id=compte_id, description=request.form['description'])
        db.session.add(trans)
        db.session.commit()
        return redirect(url_for('accueil'))
    return render_template('transaction.html', type='Dépôt', compte_id=compte_id)

@app.route('/retrait/<int:compte_id>', methods=['GET', 'POST'])
@login_required
def retrait(compte_id):
    if request.method == 'POST':
        montant = float(request.form['montant'])
        if calculer_solde(compte_id) >= montant:
            trans = Transaction(type='retrait', montant=montant, compte_id=compte_id, description=request.form['description'])
            db.session.add(trans)
            db.session.commit()
        else: flash('Solde insuffisant')
        return redirect(url_for('accueil'))
    return render_template('transaction.html', type='Retrait', compte_id=compte_id)

@app.route('/transfert', methods=['GET', 'POST'])
@login_required
def transfert():
    comptes = Compte.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        compte_src = int(request.form['compte_src'])
        compte_dest_num = request.form['compte_dest']
        montant = float(request.form['montant'])
        compte_dest = Compte.query.filter_by(numero_compte=compte_dest_num).first()
        if compte_dest and calculer_solde(compte_src) >= montant:
            trans = Transaction(type='transfert', montant=montant, compte_id=compte_src, compte_dest_id=compte_dest.id)
            db.session.add(trans)
            db.session.commit()
        else: flash('Erreur de transfert')
        return redirect(url_for('accueil'))
    return render_template('transfert.html', comptes=comptes)

@app.route('/historique/<int:compte_id>')
@login_required
def historique(compte_id):
    transactions = Transaction.query.filter((Transaction.compte_id==compte_id) | (Transaction.compte_dest_id==compte_id)).order_by(Transaction.date.desc()).all()
    return render_template('historique.html', transactions=transactions)

# --- EXPORT PDF ---
@app.route('/exporter_pdf/<int:compte_id>')
@login_required
def exporter_pdf(compte_id):
    compte = Compte.query.get(compte_id)
    transactions = Transaction.query.filter((Transaction.compte_id==compte_id) | (Transaction.compte_dest_id==compte_id)).all()
   
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
   
    elements.append(Paragraph(f"Relevé de compte: {compte.nom}", styles['h1']))
    elements.append(Spacer(1, 12))
   
    data = [['Date', 'Type', 'Montant', 'Description']]
    for t in transactions:
        data.append([t.date.strftime('%d/%m/%Y'), t.type, f"{t.montant} Gdes", t.description or ''])
   
    table = Table(data)
    table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"releve_{compte.numero_compte}.pdf")

# --- ADMIN ---
@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)

# --- CREATION DB ---
 with app.app_context():
        db.create_all()
        # Créer admin par défaut si n'existe pas
        ... 
