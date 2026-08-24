import pandas as pd
from flask import make_response
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4 
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle_secrete_banque_2026_ultra'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banque.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

import secrets # AJOUTE CET IMPORT EN HAUT

class Compte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False) # Ex: Epargne, Business
    nom_proprietaire = db.Column(db.String(100), nullable=False)
    numero_compte = db.Column(db.String(20), unique=True, nullable=False)
    password_compte = db.Column(db.String(200), nullable=False) # hash du mdp
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
        if User.query.filter_by(username=request.form['username']).first():
            flash("Nom d'utilisateur déjà pris", "danger")
            return redirect(url_for('register'))
        user = User(username=request.form['username'], password=generate_password_hash(request.form['password']))
        db.session.add(user)
        db.session.commit()
        db.session.add(Compte(nom='Principal', user_id=user.id))
        db.session.add(Compte(nom='Epargne', user_id=user.id))
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
    flash("Déconnecté", "success")
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def accueil():
    if 'user_id' not in session: return redirect(url_for('login'))

    comptes = Compte.query.filter_by(user_id=session['user_id']).all()
    compte_actif_id = int(request.args.get('compte_id', comptes[0].id if comptes else 0))

    if request.method == 'POST':
        type_op = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        compte_dest_nom = request.form.get('compte_dest', '')
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        solde_actuel = get_solde(compte_actif_id)

        if type_op in ['retrait', 'transfert_envoye'] and montant > solde_actuel:
            flash("Solde insuffisant!", "danger")
            return redirect(url_for('accueil', compte_id=compte_actif_id))

        if type_op == 'transfert_envoye':
            compte_dest = Compte.query.filter_by(nom=compte_dest_nom, user_id=session['user_id']).first()
            if not compte_dest:
                flash("Compte destination introuvable", "danger")
                return redirect(url_for('accueil', compte_id=compte_actif_id))
            db.session.add(Transaction(type='transfert_envoye', compte_id=compte_actif_id, montant=montant, description=f"Vers: {compte_dest_nom} - {description}", date=date))
            db.session.add(Transaction(type='transfert_recu', compte_id=compte_dest.id, montant=montant, description=f"De: {comptes[0].nom} - {description}", date=date))
        else:
            db.session.add(Transaction(type=type_op, compte_id=compte_actif_id, montant=montant, description=description, date=date))

        db.session.commit()
        flash(f"Opération {type_op} de {montant} Gdes effectuée", "success")
        return redirect(url_for('accueil', compte_id=compte_actif_id))

    solde = get_solde(compte_actif_id)
    transactions = Transaction.query.filter_by(compte_id=compte_actif_id).order_by(Transaction.id.desc()).limit(50).all()
    return render_template('index.html', comptes=comptes, compte_actif_id=compte_actif_id, solde=solde, transactions=transactions)

with app.app_context():
    db.create_all() 
@app.route('/creer_compte', methods=['POST'])
def creer_compte():
    if 'user_id' not in session: return redirect(url_for('login'))
    nom_compte = request.form['nom_compte']
    if Compte.query.filter_by(nom=nom_compte, user_id=session['user_id']).first():
        flash("Ce nom de compte existe déjà", "danger")
    else:
        db.session.add(Compte(nom=nom_compte, user_id=session['user_id']))
        db.session.commit()
        flash(f"Compte {nom_compte} créé!", "success")
    return redirect(url_for('accueil')) 
@app.route('/export_excel')
def export_excel():
    if 'user_id' not in session: return redirect(url_for('login'))
    compte_id = request.args.get('compte_id')
    transactions = Transaction.query.filter_by(compte_id=compte_id).all()
    compte = Compte.query.get(compte_id)

    data = [{
        "Date": t.date,
        "Type": t.type,
        "Montant": t.montant,
        "Description": t.description
    } for t in transactions]

    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name=compte.nom)
    output.seek(0)
   
    response = make_response(output.read())
    response.headers["Content-Disposition"] = f"attachment; filename=historique_{compte.nom}.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

@app.route('/export_pdf')
def export_pdf():
    if 'user_id' not in session: return redirect(url_for('login'))
    compte_id = request.args.get('compte_id')
    transactions = Transaction.query.filter_by(compte_id=compte_id).all()
    compte = Compte.query.get(compte_id)
    solde = get_solde(compte_id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, f"Relevé - Compte {compte.nom}")
    p.setFont("Helvetica", 12)
    p.drawString(50, 780, f"Solde Actuel: {solde:,.2f} Gdes")
    p.drawString(50, 760, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
   
    y = 720
    p.drawString(50, y, "Date"); p.drawString(150, y, "Type"); p.drawString(250, y, "Montant"); p.drawString(350, y, "Description")
    y -= 20
    for t in transactions:
        p.drawString(50, y, t.date)
        p.drawString(150, y, t.type)
        p.drawString(250, y, f"{t.montant:,.2f} Gdes")
        p.drawString(350, y, t.description[:30])
        y -= 20
        if y < 50: p.showPage(); y = 800
   
    p.showPage()
    p.save()
    buffer.seek(0)
    return response.send_file(buffer, as_attachment=True, download_name=f"releve_{compte.nom}.pdf", mimetype='application/pdf') 
