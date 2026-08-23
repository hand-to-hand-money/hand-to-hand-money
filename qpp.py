from flask import Flask, render_template_string, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
import bcrypt

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

HOME_HTML = """ ...même code qu'avant... """
FORM_HTML = """ ...même code qu'avant... """

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 
