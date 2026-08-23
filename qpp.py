from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
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

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/demande")
def demande():
    return "<h1>Formulaire arrive bientôt</h1><a href='/'>Retour</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 
