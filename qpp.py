from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle_secrete_banque_2026_ultra'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banque.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Compte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False) # Principal, Epargne
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    compte_id = db.Column(db.Integer, db.ForeignKey('compte.id'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)

def get_solde(compte_id):
    depots = db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.compte_id==compte_id, Transaction.type.in_(['depot', 'pret', 'transfert_recu'])).scalar() or 0
    retraits = db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.compte_id==compte_id, Transaction.type.in_(['retrait', 'transfert_envoye'])).scalar() or 0
    return depots - retraits

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'], password=generate_password_hash(request.form['password']))
        db.session.add(user)
        db.session.commit()
        # Créer compte Principal par défaut
        db.session.add(Compte(nom='Principal', user_id=user.id))
        db.session.commit()
        flash("Compte créé! Connectez-vous", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('accueil'))
        flash("Identifiants incorrects", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def accueil():
    if 'user_id' not in session: return redirect(url_for('login'))

    comptes = Compte.query.filter_by(user_id=session['user_id']).all()
    compte_actif_id = request.args.get('compte_id', comptes[0].id if comptes else None)

    if request.method == 'POST':
        #... même logique que avant mais avec compte_id...
        pass # Je te donne le code complet si tu veux

    solde = get_solde(compte_actif_id)
    transactions = Transaction.query.filter_by(compte_id=compte_actif_id).order_by(Transaction.id.desc()).all()
    return render_template('index.html', comptes=comptes, compte_actif_id=int(compte_actif_id), solde=solde, transactions=transactions)

with app.app_context():
    db.create_all() 
