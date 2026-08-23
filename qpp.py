from flask import Flask, render_template_string, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Demande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    montant = db.Column(db.Integer, nullable=False)
    raison = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Argent de Poche</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #f0f8ff; }
        h1 { color: #2c3e50; }
        .btn { background: #27ae60; color: white; padding: 15px 30px; text-decoration: none;
               border-radius: 8px; font-size: 18px; display: inline-block; margin-top: 20px; }
        .btn:hover { background: #229954; }
    </style>
</head>
<body>
    <h1>💰 Bienvenue sur Argent de Poche 💰</h1>
    <p>Gagne de l'argent facilement avec des petites tâches</p>
    <a href="/demande" class="btn">Faire une demande</a>
</body>
</html>
"""

FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Faire une demande</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; padding: 30px; background: #f0f8ff; max-width: 500px; margin: auto; }
        h1 { color: #2c3e50; text-align: center; }
        input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .btn { background: #27ae60; color: white; padding: 15px; border: none;
               border-radius: 8px; font-size: 16px; width: 100%; cursor: pointer; }
        .btn:hover { background: #229954; }
    </style>
</head>
<body>
    <h1>📝 Faire une demande</h1>
    <form method="POST">
        <label>Nom complet :</label>
        <input type="text" name="nom" required>
       
        <label>WhatsApp :</label>
        <input type="tel" name="whatsapp" required>
       
        <label>Montant demandé (FCFA) :</label>
        <input type="number" name="montant" required>
       
        <label>Pourquoi tu as besoin d'argent :</label>
        <textarea name="raison" rows="4" required></textarea>
       
        <button type="submit" class="btn">Envoyer ma demande</button>
    </form>
    <br>
    <a href="/">Retour à l'accueil</a>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Demandes</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        h1 { color: #c0392b; text-align: center; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #2c3e50; color: white; }
        tr:nth-child(even) { background: #f2f2f2; }
    </style>
</head>
<body>
    <h1>📊 Tableau des Demandes - Argent de Poche</h1>
    <table>
        <tr>
            <th>ID</th><th>Nom</th><th>WhatsApp</th><th>Montant FCFA</th><th>Raison</th>
        </tr>
        {% for d in demandes %}
        <tr>
            <td>{{ d.id }}</td><td>{{ d.nom }}</td><td>{{ d.whatsapp }}</td><td>{{ d.montant }}</td><td>{{ d.raison }}</td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="/">Retour Accueil</a>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/demande", methods=["GET", "POST"])
def demande():
    if request.method == "POST":
        nouvelle_demande = Demande(
            nom=request.form.get("nom"),
            whatsapp=request.form.get("whatsapp"),
            montant=request.form.get("montant"),
            raison=request.form.get("raison")
        )
        db.session.add(nouvelle_demande)
        db.session.commit()
        return f"<h1>Merci {nouvelle_demande.nom} !</h1><p>Ta demande de {nouvelle_demande.montant} FCFA a été reçue.</p><a href='/'>Retour</a>"
    return render_template_string(FORM_HTML)

from functools import wraps
from flask import request, Response

# TES IDENTIFIANTS ADMIN
USERNAME = "1-hthadmin"
PASSWORD = "Ljr8098933112*"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
    'Accès refusé. Il faut se connecter.',
    401,
    {'WWW-Authenticate': 'Basic realm="Admin Argent de Poche"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/admin")
@requires_auth
def admin():
    toutes_demandes = Demande.query.all()
    return render_template_string(ADMIN_HTML, demandes=toutes_demandes) 
