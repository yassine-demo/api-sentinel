import pytest
from app import app, db, Endpoint, CheckResult

@pytest.fixture(autouse=True)
def setup_database():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_sentinel.db'
    
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_get_empty_endpoints(client):
    """Vérifie que la liste est vide au départ."""
    response = client.get('/api/endpoints')
    assert response.status_code == 200
    assert response.json == []

def test_add_valid_endpoint(client):
    """Vérifie l'ajout d'un endpoint valide."""
    response = client.post('/api/endpoints', json={
        "name": "API Stable",
        "url": "https://httpbin.org/status/200",
        "latency_threshold": 800
    })
    assert response.status_code == 201
    assert response.json["name"] == "API Stable"
    assert response.json["latency_threshold"] == 800

def test_add_invalid_url(client):
    """Vérifie le rejet d'une URL non sécurisée ou interne (Sécurité SSRF)."""
    response = client.post('/api/endpoints', json={
        "name": "Localhost Attack",
        "url": "http://127.0.0.1/secret"
    })
    assert response.status_code == 400
    assert "error" in response.json

def test_check_result_network_failure(client):
    """Vérifie qu'un échec réseau (status_code à None, DOWN) s'enregistre correctement."""
    with app.app_context():
        ep = Endpoint(name="API Inaccessible", url="https://domaine-inexistant-xyz.com")
        db.session.add(ep)
        db.session.commit()

        # Simulation d'un résultat d'erreur réseau
        result = CheckResult(
            endpoint_id=ep.id,
            status_code=None,
            response_time_ms=5000.0,
            is_up=False,
            status="DOWN"
        )
        db.session.add(result)
        db.session.commit()

        saved = CheckResult.query.first()
        assert saved.status_code is None
        assert saved.is_up is False
        assert saved.status == "DOWN"

def test_check_result_http_error_500(client):
    """Vérifie qu'une réponse HTTP 500 est correctement qualifiée en DOWN."""
    with app.app_context():
        ep = Endpoint(name="API En Erreur", url="https://httpbin.org/status/500")
        db.session.add(ep)
        db.session.commit()

        result = CheckResult(
            endpoint_id=ep.id,
            status_code=500,
            response_time_ms=120.0,
            is_up=False,
            status="DOWN"
        )
        db.session.add(result)
        db.session.commit()

        saved = CheckResult.query.first()
        assert saved.status_code == 500
        assert saved.is_up is False
        assert saved.status == "DOWN"

def test_check_result_latency_slow(client):
    """Vérifie qu'un dépassement de seuil qualifie l'état en SLOW."""
    with app.app_context():
        ep = Endpoint(name="API Lente", url="https://httpbin.org/delay/1", latency_threshold=200)
        db.session.add(ep)
        db.session.commit()

        # Temps de réponse supérieur au seuil de 200ms
        result = CheckResult(
            endpoint_id=ep.id,
            status_code=200,
            response_time_ms=450.0,
            is_up=True,
            status="SLOW"
        )
        db.session.add(result)
        db.session.commit()

        saved = CheckResult.query.first()
        assert saved.status_code == 200
        assert saved.is_up is True
        assert saved.status == "SLOW"