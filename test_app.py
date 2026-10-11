import pytest
from app import app, db, Endpoint

@pytest.fixture
def client():
    """
    configuration de l'app Flask pour les tests en utilisant 
    une base de données temporaire en mémoire (isolée de la prod)
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()  # client de test pour simuler les requêtes HTTP
        db.drop_all()

def test_get_empty_endpoints(client):
    """ verifie la liste des endpoints est vide au départ """
    response = client.get('/api/endpoints')
    assert response.status_code == 200
    assert response.json == []

def test_add_endpoint(client):
    """ verifie qu'on peut ajouter un nouvel endpoint via l'API REST"""
    response = client.post('/api/endpoints', json={
        "name": "API Test Unitaire",
        "url": "https://httpbin.org/status/200",
        "latency_threshold": 400
    })
    
    #201 = Created, l'endpoint a été ajouté avec succès
    assert response.status_code == 201
    data = response.json
    assert data["name"] == "API Test Unitaire"
    assert data["url"] == "https://httpbin.org/status/200"
    assert data["latency_threshold"] == 400

    #verifie que l'endpoint apparaît bien dans la liste générale
    res_get = client.get('/api/endpoints')
    assert len(res_get.json) == 1

def test_delete_endpoint(client):
    """ verifie qu'on peut supprimer un endpoint existant"""
    #1. ajouter un endpoint pour pouvoir le supprimer ensuite
    res_post = client.post('/api/endpoints', json={
        "name": "À supprimer",
        "url": "https://httpbin.org/status/200"
    })
    endpoint_id = res_post.json["id"]

    #2. envoyer la requête de suppression
    res_del = client.delete(f'/api/endpoints/{endpoint_id}')
    assert res_del.status_code == 200

    #3. verifier que la liste est de nouveau vide
    res_get = client.get('/api/endpoints')
    assert res_get.json == []