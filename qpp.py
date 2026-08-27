from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'une_cle_secrete_tres_longue_et_aleatoire'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ===== MODELES =====
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    comptes = db.relationship('Compte', backref='proprietaire', lazy=True)

class Compte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transactions = db.relationship('Transaction', backref='compte', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False) # depot, retrait, transfert_sortant, transfert_entrant
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    compte_id = db.Column(db.Integer, db.ForeignKey('compte.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== FONCTIONS =====
def calculer_solde(compte_id):
    depots = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='depot').scalar() or 0
    retraits = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='retrait').scalar() or 0
    sortants = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='transfert_sortant').scalar() or 0
    entrants = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='transfert_entrant').scalar() or 0
    return depots - retraits - sortants + entrants

# ===== ROUTES =====
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('accueil'))
        flash('Identifiants incorrects')
    return render_template('login.html')

@app.route('/accueil')
@login_required
def accueil():
    comptes = Compte.query.filter_by(user_id=current_user.id).all()
    soldes = {c.id: calculer_solde(c.id) for c in comptes}
    solde_total = sum(soldes.values())
    return render_template('accueil.html', comptes=comptes, soldes=soldes, solde_total=solde_total)

@app.route('/ajouter_compte', methods=['GET', 'POST'])
@login_required
def ajouter_compte():
    if request.method == 'POST':
        nouveau = Compte(nom=request.form['nom'], user_id=current_user.id)
        db.session.add(nouveau)
        db.session.commit()
        return redirect(url_for('accueil'))
    return render_template('ajouter_compte.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ===== CREATION DB =====
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin créé: admin / admin123")

if __name__ == '__main__':
    app.run
