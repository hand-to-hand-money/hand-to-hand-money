from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)

# Config Base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///depenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Récupère les infos depuis Render Environment
TON_EMAIL = os.environ.get('TON_EMAIL')
MOT_DE_PASSE_APP = os.environ.get('MOT_DE_PASSE_APP')

# Modèle de la base de données
class Depense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)

# Fonction pour envoyer l'email
def envoyer_email_notif(nom, montant):
    if not TON_EMAIL or not MOT_DE_PASSE_APP:
        print("ERREUR: Variables TON_EMAIL ou MOT_DE_PASSE_APP non définies dans Render")
        return
    try:
        msg = MIMEText(f"Nouvelle dépense enregistrée:\n\nNom: {nom}\nMontant: {montant} Gdes")
        msg['Subject'] = 'Nouvelle Dépense - Hand to Hand Money'
        msg['From'] = TON_EMAIL
        msg['To'] = TON_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(TON_EMAIL, MOT_DE_PASSE_APP)
            server.send_message(msg)
        print("Email envoyé avec succès")
    except Exception as e:
        print(f"Erreur envoi email: {e}")

# Route principale
@app.route('/', methods=['GET', 'POST'])
def accueil():
    if request.method == 'POST':
        nom = request.form['nom']
        montant = float(request.form['montant'])
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
       
        nouvelle_depense = Depense(nom=nom, montant=montant, date=date)
        db.session.add(nouvelle_depense)
        db.session.commit()
       
        envoyer_email_notif(nom, montant)
        return redirect(url_for('accueil'))
   
    depenses = Depense.query.order_by(Depense.id.desc()).all()
    total = sum(d.montant for d in depenses)
    return render_template('index.html', depenses=depenses, total=total)

# Crée la base de données au démarrage
with app.app_context():
    db.create_all() 
