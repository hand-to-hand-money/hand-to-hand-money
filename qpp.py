 from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask import Response
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///depenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIG NOTIF EMAIL
TON_EMAIL = os.environ.get('ljuanriccardo@gmail.com')
MOT_DE_PASSE_APP = os.environ.get('spnlrxmsizflifwz')

class Depense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    montant = db.Column(db.Float)
    date = db.Column(db.String(20)) 

