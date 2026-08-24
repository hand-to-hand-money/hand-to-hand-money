from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle_secrete_banque_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banque.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False) # depot, retrait, pret, transfert_envoye, transfert_recu
    compte = db.Column(db.String(50), nullable=False, default='Principal') # pour gérer plusieurs comptes plus tard
    montant = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)

def get_solde():
    depots = db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.type.in_(['depot', 'pret', 'transfert_recu'])).scalar() or 0
    retraits = db.session.query(db.func.sum(Transaction.montant)).filter(Transaction.type.in_(['retrait', 'transfert_envoye'])).scalar() or 0
    return depots - retraits

@app.route('/', methods=['GET', 'POST'])
def accueil():
    if request.method == 'POST':
        type_op = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        compte_dest = request.form.get('compte_dest', '')
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        solde_actuel = get_solde()

        # Vérifs
        if type_op in ['retrait', 'transfert_envoye'] and montant > solde_actuel:
            flash("Solde insuffisant !", "danger")
            return redirect(url_for('accueil'))

        # Enregistrer la transaction
        if type_op == 'transfert_envoye':
            db.session.add(Transaction(type='transfert_envoye', montant=montant, description=f"Vers: {compte_dest} - {description}", date=date))
            db.session.add(Transaction(type='transfert_recu', montant=montant, description=f"De: Principal - {description}", compte=compte_dest, date=date))
        else:
            db.session.add(Transaction(type=type_op, montant=montant, description=description, date=date))
       
        db.session.commit()
        flash(f"Opération {type_op} de {montant} Gdes effectuée", "success")
        return redirect(url_for('accueil'))
   
    transactions = Transaction.query.order_by(Transaction.id.desc()).limit(50).all()
    solde = get_solde()
   
    return render_template('index.html', transactions=transactions, solde=solde)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 
