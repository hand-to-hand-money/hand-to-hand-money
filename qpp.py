from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask import Response
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///depenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'une_cle_secrete_tres_longue'
db = SQLAlchemy(app)


# CONFIG NOTIF EMAIL - Récupéré depuis Render
TON_EMAIL = os.environ.get('TON_EMAIL')
MOT_DE_PASSE_APP = os.environ.get('MOT_DE_PASSE_APP')


class Depense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)


def envoyer_email_notif(nom, montant):
    if not TON_EMAIL or not MOT_DE_PASSE_APP:
        print("ERREUR: Variables email non définies sur Render")
        return
       
    try:
        msg = MIMEText(f"Nouvelle dépense ajoutée:\n\nNom: {nom}\nMontant: {montant} Gdes")
        msg['Subject'] = 'Nouvelle Dépense Hand-to-Hand'
        msg['From'] = TON_EMAIL
        msg['To'] = TON_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(TON_EMAIL, MOT_DE_PASSE_APP)
            server.send_message(msg)
        print("Email envoyé avec succès")
    except Exception as e:
        print(f"Erreur envoi email: {e}")


@app.route('/', methods=['GET', 'POST'])
def accueil():
    if request.method == 'POST':
        nom = request.form['nom']
        montant = float(request.form['montant'])
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
       
        nouvelle_depense = Depense(nom=nom, montant=montant, date=date)
        db.session.add(nouvelle_depense)
        db.session.commit()
       
        envoyer_email_notif(nom, montant) # Envoie l'email
        return redirect(url_for('accueil'))

    depenses = Depense.query.order_by(Depense.id.desc()).all()
    total = sum(d.montant for d in depenses)
    return render_template('index.html', depenses=depenses, total=total)


with app.app_context():
    db.create_all() # Crée la base de données au démarrage


if __name__ == '__main__':
    app.run(debug=True) 
