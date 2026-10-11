from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import requests
import time
from apscheduler.schedulers.background import BackgroundScheduler


#initialisation de l'app FLASK
app = Flask(__name__)

#config de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sentinel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#création du modèle de données
class Endpoint(db.Model):
    """
    cette table va stocker la liste des API à surveiller
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)

    #seuil en milisecondes pour considérer que l'API est lente
    latency_threshold = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """
        convertit l'objet en dictionnaire pour faciliter l'envoi en JSON (API REST)
        """
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "latency_threshold": self.latency_threshold,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
   

class CheckResult(db.Model):
    """
    cette table stocke l'historique des vérifications effectuée
    """
    id = db.Column(db.Integer, primary_key=True)
    endpoint_id = db.Column(db.Integer, db.ForeignKey('endpoint.id'), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Float, nullable=False)
    is_up = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default= lambda: datetime.now(timezone.utc))

    endpoint = db.relationship('Endpoint', backref=db.backref('results', lazy=True))

    def to_dict(self):
        """
        convertit l'objet en dictionnaire pour faciliter l'envoi en JSON (API REST)
        """
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "is_up": self.is_up,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
#moteur de vérification HTTP (arriére plan)
def check_endpoints():
    """
    parcourt chaque endpoint & mesure le temps de réponse HTTP & enregustre le résultat dans SQLite
    """
    with app.app_context():
        endpoints = Endpoint.query.all()
        if not endpoints:
            print("**Sentinel** : Aucun endpoint à surveiller pour le moment.")
            return

        print (f"**Sentinel** : Vérification en cours de {len(endpoints)} endpoint(s)...")

        for ep in endpoints:
            start_time = time.time()
            try:
                #timeoout = 5 secondes --> pour éviter de bloquer indéfiniment si l'API ne répond pas
                response = requests.get(ep.url, timeout=5)
                duration_ms = round((time.time() - start_time) * 1000, 2)
                status_code = response.status_code
                is_up = 200 <= status_code < 300

            except requests.RequestException as e:
                #capture des erreurs de connexion, timeout, etc.
                duration_ms = round((time.time() - start_time) * 1000, 2)
                status_code = None
                is_up = False

            #enregistrement du résultat dans la base de données
            result = CheckResult(
                endpoint_id=ep.id,
                status_code=status_code,
                response_time_ms=duration_ms,
                is_up=is_up
            )
            db.session.add(result)
            db.session.commit()

            status_label = "UP" if is_up else "DOWN"
            print(f" --> [{status_label}] {ep.name} | Code: {status_code} | Temps de réponse: {duration_ms} ms")

#configuration du planificateur de tâches (scheduler)
#exection de la fonction toutes les 30 secondes
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_endpoints, trigger="interval", seconds=30)
scheduler.start()


#routes API REST (gestion des Endpoints) & interface web
@app.route('/')
def index():
    """
    page d'accueil de l'interface web
    """
    return render_template('index.html')


#consultation de la liste des endpoints(GET)
@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    endpoints = Endpoint.query.all()
    return jsonify([ep.to_dict() for ep in endpoints]), 200

#ajouter un nouvel endpoint (POST)
@app.route('/api/endpoints', methods=['POST'])
def add_endpoint():
    data = request.get_json()

    if not data or 'name' not in data or 'url' not in data:
        return jsonify({"error": "Les champs 'name' et 'url' sont obligatoires."}), 400

    new_endpoint = Endpoint(
        name = data['name'],
        url = data['url'],
        latency_threshold = data.get('latency_threshold', 1000)
    )

    db.session.add( new_endpoint)
    db.session.commit()

    return jsonify(new_endpoint.to_dict()), 201

#supprimer un endpoint (DELETE)
@app.route('/api/endpoints/<int:endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    endpoint = Endpoint.query.get_or_404(endpoint_id)
    db.session.delete(endpoint)
    db.session.commit()

    return jsonify({"message": f"Endpoint {endpoint_id} supprimé avec succès."}), 200


#obtenir les 50 derniers résultats de vérification
@app.route('/api/results', methods=['GET'])
def get_results():
    results = CheckResult.query.order_by (CheckResult.timestamp.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in results]), 200



#initialisation de la base de données
with app.app_context():
    db.create_all()
    print("Base de données initialisée avec succès !")

#demarrage du serveur 
if __name__ == '__main__':
    try:
        app.run(debug=True, use_reloader=False)  # use_reloader=False--> éviter l'exécution double du scheduler
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler arrêté! Serveur Flask terminé.")