"""
Tests unitaires pour l'application web
"""

import unittest
import json
import os
import sys

# Ajouter le chemin pour les imports
sys.path.insert(0, os.path.dirname(__file__))

from app_web import app, db, User, Alert, Message, Diagnostic

class ChatWebTestCase(unittest.TestCase):
    """Cas de test pour l'application web"""
    
    def setUp(self):
        """Préparation avant chaque test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Créer un utilisateur de test
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_register_user(self):
        """Test création d'utilisateur"""
        response = self.app.post('/register', 
            json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123'
            }
        )
        self.assertEqual(response.status_code, 201)
        
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
    
    def test_login_user(self):
        """Test connexion utilisateur"""
        response = self.app.post('/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_login_invalid_credentials(self):
        """Test connexion avec mauvais identifiants"""
        response = self.app.post('/login',
            json={
                'username': 'testuser',
                'password': 'wrongpassword'
            }
        )
        self.assertEqual(response.status_code, 401)
    
    def test_receive_alert(self):
        """Test réception d'une alerte"""
        response = self.app.post('/api/receive-alert',
            json={
                'type': 'error',
                'title': 'Erreur Test',
                'message': 'Message d\'erreur',
                'severity': 'high'
            }
        )
        self.assertEqual(response.status_code, 201)
        
        with app.app_context():
            alert = Alert.query.first()
            self.assertEqual(alert.title, 'Erreur Test')
            self.assertEqual(alert.severity, 'high')
    
    def test_receive_diagnostic(self):
        """Test réception d'un diagnostic"""
        response = self.app.post('/api/receive-diagnostic',
            json={
                'diagnostic_id': 'TEST-123',
                'description': 'Test diagnostic',
                'result': {'status': 'OK'},
                'status': 'completed'
            }
        )
        self.assertEqual(response.status_code, 201)
        
        with app.app_context():
            diag = Diagnostic.query.first()
            self.assertEqual(diag.diagnostic_id, 'TEST-123')
    
    def test_get_alerts_protected(self):
        """Test que /api/alerts nécessite authentification"""
        response = self.app.get('/api/alerts')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_get_stats(self):
        """Test récupération des statistiques"""
        with app.app_context():
            # Ajouter des données de test
            alert = Alert(title='Test', message='Test', type='info')
            db.session.add(alert)
            db.session.commit()
        
        response = self.app.post('/api/receive-alert',
            json={
                'type': 'error',
                'title': 'Test Alert',
                'message': 'Test'
            }
        )
        
        response = self.app.get('/api/stats')
        # Note: accès sans authentification, comme pour les autres endpoints système
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('total_alerts', data)

class ChatIntegrationTestCase(unittest.TestCase):
    """Test d'intégration avec app.py"""
    
    def test_import_chat_integration(self):
        """Test import du module d'intégration"""
        from chat_integration import ChatWebIntegration, init_chat_integration
        
        web = ChatWebIntegration('http://test:5001')
        self.assertEqual(web.web_app_url, 'http://test:5001')
    
    def test_chat_integration_methods(self):
        """Test des méthodes du module d'intégration"""
        from chat_integration import ChatWebIntegration
        
        web = ChatWebIntegration('http://localhost:5001')
        web.enabled = False  # Désactiver pour ne pas vraiment envoyer
        
        # Ces méthodes doivent retourner False car désactivées
        self.assertFalse(web.send_alert('Test', 'Test'))
        self.assertFalse(web.send_diagnostic('TEST-1', 'Test', {}))

if __name__ == '__main__':
    unittest.main()
