from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import requests
import time
from urllib.parse import urlparse
from apscheduler.schedulers.background import BackgroundScheduler

# initialisation de l'application
app = Flask(__name__)

# configuration de sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sentinel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# modèle des endpoints surveillés
class Endpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    latency_threshold = db.Column(db.Integer, default=1000)  # seuil en ms
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "latency_threshold": self.latency_threshold,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }


# résultat d'un contrôle effectué sur un endpoint
class CheckResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint_id = db.Column(
        db.Integer,
        db.ForeignKey('endpoint.id'),
        nullable=False
    )

    # peut être vide si la requête échoue avant d'obtenir une réponse
    status_code = db.Column(db.Integer, nullable=True)

    response_time_ms = db.Column(db.Float, nullable=False)
    is_up = db.Column(db.Boolean, nullable=False)

    # UP : disponible
    # SLOW : disponible mais lent
    # DOWN : indisponible
    status = db.Column(db.String(20), default="UP")

    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    endpoint = db.relationship(
        'Endpoint',
        backref=db.backref('results', lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "is_up": self.is_up,
            "status": self.status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }


# vérifie que l'url est autorisée
def is_safe_url(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ('http', 'https'):
            return False

        hostname = parsed.hostname

        if not hostname:
            return False

        # on bloque les adresses locales
        if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
            return False

        return True

    except Exception:
        return False


# contrôle tous les endpoints enregistrés
def check_endpoints():
    with app.app_context():
        endpoints = Endpoint.query.all()

        if not endpoints:
            return

        for ep in endpoints:
            start_time = time.time()

            try:
                response = requests.get(
                    ep.url,
                    timeout=5,
                    allow_redirects=True
                )

                duration_ms = round(
                    (time.time() - start_time) * 1000,
                    2
                )

                status_code = response.status_code

                # endpoint disponible
                if 200 <= status_code < 300:
                    is_up = True

                    if duration_ms > ep.latency_threshold:
                        status_label = "SLOW"
                    else:
                        status_label = "UP"

                else:
                    is_up = False
                    status_label = "DOWN"

            except requests.RequestException:
                # erreur réseau ou timeout
                duration_ms = round(
                    (time.time() - start_time) * 1000,
                    2
                )

                status_code = None
                is_up = False
                status_label = "DOWN"

            result = CheckResult(
                endpoint_id=ep.id,
                status_code=status_code,
                response_time_ms=duration_ms,
                is_up=is_up,
                status=status_label
            )

            db.session.add(result)
            db.session.commit()


# démarrage du scheduler
scheduler = BackgroundScheduler()

if not app.config.get('TESTING'):
    scheduler.add_job(
        func=check_endpoints,
        trigger="interval",
        seconds=30
    )
    scheduler.start()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    endpoints = Endpoint.query.all()
    return jsonify([ep.to_dict() for ep in endpoints]), 200


@app.route('/api/endpoints', methods=['POST'])
def add_endpoint():
    data = request.get_json()

    if not data or 'name' not in data or 'url' not in data:
        return jsonify({
            "error": "les champs 'name' et 'url' sont obligatoires"
        }), 400

    url = data['url']

    # vérification de l'url avant enregistrement
    if not is_safe_url(url):
        return jsonify({
            "error": "url invalide ou non autorisée"
        }), 400

    new_endpoint = Endpoint(
        name=data['name'],
        url=url,
        latency_threshold=data.get('latency_threshold', 1000)
    )

    db.session.add(new_endpoint)
    db.session.commit()

    return jsonify(new_endpoint.to_dict()), 201


@app.route('/api/endpoints/<int:endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    endpoint = Endpoint.query.get_or_404(endpoint_id)

    # suppression de l'historique associé
    CheckResult.query.filter_by(
        endpoint_id=endpoint.id
    ).delete()

    db.session.delete(endpoint)
    db.session.commit()

    return jsonify({
        "message": f"endpoint {endpoint_id} supprimé"
    }), 200


@app.route('/api/results', methods=['GET'])
def get_results():
    results = (
        CheckResult.query
        .order_by(CheckResult.timestamp.desc())
        .limit(50)
        .all()
    )

    return jsonify([
        r.to_dict() for r in results
    ]), 200


# création des tables au démarrage
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    try:
        app.run(debug=True, use_reloader=False)

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()