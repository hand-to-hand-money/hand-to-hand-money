from flask import Flask, render_template, request, redirect, url_for, flash
app = Flask(__name__)
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'banque_secrete_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banque.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

FRAIS_POURCENTAGE = 0.01
FRAIS_MIN = 100
TAUX_INTERET = 5.0

class Client(UserMixin, db.Model):
    id = db.Column(db.String(20), primary_key=True)
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    mdp_hash = db.Column(db.String(200))
    statut = db.Column(db.String(20), default="actif")

class Compte(db.Model):
    numero = db.Column(db.String(20), primary_key=True)
    client_id = db.Column(db.String(20), db.ForeignKey('client.id'))
    solde = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    compte_numero = db.Column(db.String(20))
    type = db.Column(db.String(50))
    montant = db.Column(db.Float)
    frais = db.Column(db.Float, default=0)
    date = db.Column(db.DateTime, default=datetime.now)
    details = db.Column(db.String(200))

class Pret(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    client_id = db.Column(db.String(20))
    montant = db.Column(db.Float)
    duree_mois = db.Column(db.Integer)
    mensualite = db.Column(db.Float)
    statut = db.Column(db.String(20), default="en attente")
    date_demande = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(user_id)

def calculer_frais(montant):
    return max(montant * FRAIS_POURCENTAGE, FRAIS_MIN)

def calculer_mensualite(montant, duree):
    taux_mensuel = (TAUX_INTERET / 100) / 12
    return round(montant * (taux_mensuel * (1 + taux_mensuel)**duree) / ((1 + taux_mensuel)**duree - 1), 2)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom, email, mdp = request.form['nom'], request.form['email'], request.form['mdp']
        if Client.query.filter_by(email=email).first():
            flash("Cet email existe déjà", "danger")
            return redirect(url_for('register'))
        client_id = str(uuid.uuid4())[:8]
        num_compte = "CPT" + client_id
        mdp_hash = bcrypt.hashpw(mdp.encode(), bcrypt.gensalt())
        db.session.add(Client(id=client_id, nom=nom, email=email, mdp_hash=mdp_hash))
        db.session.add(Compte(numero=num_compte, client_id=client_id))
        db.session.commit()
        flash("Compte créé! Connecte-toi", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        client = Client.query.filter_by(email=request.form['email']).first()
        if client and bcrypt.checkpw(request.form['mdp'].encode(), client.mdp_hash):
            login_user(client)
            return redirect(url_for('admin') if client.id == "ADMIN001" else url_for('dashboard'))
        else: flash("Identifiants incorrects", "danger")
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    compte = Compte.query.filter_by(client_id=current_user.id).first()
    transactions = Transaction.query.filter_by(compte_numero=compte.numero).order_by(Transaction.date.desc()).limit(10).all()
    prets = Pret.query.filter_by(client_id=current_user.id).all()
    return render_template('dashboard.html', compte=compte, transactions=transactions, prets=prets)

@app.route('/action', methods=['POST'])
@login_required
def action():
    compte = Compte.query.filter_by(client_id=current_user.id).first()
    action_type = request.form['action_type']
    montant = float(request.form['montant'])
    frais = calculer_frais(montant)
    # ... le reste du code des actions ...
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin():
    if current_user.id != "ADMIN001": return "Accès refusé"
    clients = db.session.query(Client, Compte).join(Compte).all()
    prets = Pret.query.filter_by(statut="en attente").all()
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(20).all()
    return render_template('admin.html', clients=clients, prets=prets, transactions=transactions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/')
def home():
    return "<h1>Bienvennue sur Argent de poche </h1>"
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
    with app.app_context():
        db.create_all()
        if not Client.query.get("ADMIN001"):
            mdp_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
            db.session.add(Client(id="ADMIN001", nom="Admin", email="admin@banque.com", mdp_hash=mdp_hash))
            db.session.add(Compte(numero="CPTADMIN001", client_id="ADMIN001", solde=1000000))
            db.session.commit()
    app.run() 
