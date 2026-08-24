from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io
import secrets
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.config['SECRET_KEY'] = 'une_cle_secrete_tres_longue'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banque.db'
db = SQLAlchemy(app)

ADMIN_USERNAME = "admin"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Compte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    nom_proprietaire = db.Column(db.String(100), nullable=False)
    numero_compte = db.Column(db.String(20), unique=True, nullable=False)
    password_compte = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    compte_id = db.Column(db.Integer, db.ForeignKey('compte.id'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

def generer_numero_compte():
    return "HTH" + str(secrets.randbelow(90000000) + 10000000)

def calculer_solde(compte_id):
    depots = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='depot').scalar() or 0
    retraits = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='retrait').scalar() or 0
    envoye = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='transfert_envoye').scalar() or 0
    recu = db.session.query(db.func.sum(Transaction.montant)).filter_by(compte_id=compte_id, type='transfert_recu').scalar() or 0
    return depots + recu - retraits - envoye

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.username != ADMIN_USERNAME:
        flash("Accès refusé", "danger")
        return redirect(url_for('accueil'))
    users = User.query.all()
    comptes = Compte.query.all()
    transactions = Transaction.query.order_by(Transaction.id.desc()).limit(50).all()
    return render_template('admin.html', users=users, comptes=comptes, transactions=transactions)

# ... colle ici toutes tes autres routes: login, register, accueil, exporter_pdf etc en version Python correcte 
with app.app_context():
        db.drop_all()  # <-- CA SUPPRIME L'ANCIENNE DB
        db.create_all() # <-- CA RECREE AVEC LES NOUVELLES COLONNES
        print("Base de données recréée!") 
