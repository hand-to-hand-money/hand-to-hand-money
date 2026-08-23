from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

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

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/demande", methods=["GET", "POST"])
def demande():
    if request.method == "POST":
        nom = request.form.get("nom")
        return f"<h1>Merci {nom} !</h1><p>Ta demande a été reçue. On te contacte sur WhatsApp.</p><a href='/'>Retour</a>"
    return render_template_string(FORM_HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 

