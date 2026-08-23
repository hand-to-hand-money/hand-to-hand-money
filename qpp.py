from flask import Flask, render_template_string, request
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask import Response
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CONFIG NOTIF EMAIL - CHANGE ÇA
TON_EMAIL = "ton.email@gmail.com"  # L'email où tu veux recevoir les notifs
MOT_DE_PASSE_APP = "abcd efgh ijkl mnop" # Le code de 16 caractères de Google

class Demande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    montant = db.Column(db.Integer, nullable=False)
    raison = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

# IDENTIFIANTS ADMIN
USERNAME = "1-hthadmin"
PASSWORD = "Ljr8098933112*"

def check_auth(username, password): return username == USERNAME and password == PASSWORD
def authenticate(): return Response('Accès refusé.', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password): return authenticate()
        return f(*args, **kwargs)
    return decorated

def envoyer_email(demande):
    sujet = f"NOUVELLE DEMANDE: {demande.nom} - {demande.montant} FCFA"
    corps = f"""
    Nouvelle demande reçue !
   
    Nom: {demande.nom}
    WhatsApp: {demande.whatsapp}
    Montant: {demande.montant} FCFA
    Raison: {demande.raison}
    """
    msg = MIMEText(corps)
    msg['Subject'] = sujet
    msg['From'] = TON_EMAIL
    msg['To'] = TON_EMAIL
   
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(TON_EMAIL, MOT_DE_PASSE_APP)
        server.send_message(msg)
        server.quit()
        print("Email envoyé !")
    except Exception as e:
        print(f"Erreur email: {e}")

HOME_HTML = """...même code qu'avant..."""
FORM_HTML = """...même code qu'avant..."""
ADMIN_HTML = """...même code qu'avant..."""

@app.route("/")
def home(): return render_template_string(HOME_HTML)

@app.route("/demande", methods=["GET", "POST"])
def demande():
    if request.method == "POST":
        nouvelle_demande = Demande(nom=request.form.get("nom"), whatsapp=request.form.get("whatsapp"), montant=request.form.get("montant"), raison=request.form.get("raison"))
        db.session.add(nouvelle_demande)
        db.session.commit()
       
        envoyer_email(nouvelle_demande) # <-- ON ENVOIE LA NOTIF ICI
       
        return f"<h1>Merci {nouvelle_demande.nom} !</h1><p>Ta demande de {nouvelle_demande.montant} FCFA a été reçue.</p><a href='/'>Retour</a>"
    return render_template_string(FORM_HTML)

@app.route("/admin")
@requires_auth
def admin():
    toutes_demandes = Demande.query.all()
    return render_template_string(ADMIN_HTML, demandes=toutes_demandes)

if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 
