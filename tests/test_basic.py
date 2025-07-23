import unittest
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User


class BasicTestCase(unittest.TestCase):
    """Basic test cases for the Corps Attendance System"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        """Test that the application instance exists"""
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        """Test that the application is in testing mode"""
        self.assertTrue(self.app.config['TESTING'])

    def test_home_page(self):
        """Test that the home page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_admin_redirect(self):
        """Test that admin pages require authentication"""
        response = self.client.get('/admin/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_user_model(self):
        """Test basic user model functionality"""
        user = User(
            state_code='TEST001',
            full_name='Test User',
            email='test@example.com',
            is_admin=False,
            is_active=True
        )
        user.set_password('testpass')
        user.set_pin('1234')
        
        db.session.add(user)
        db.session.commit()
        
        # Test password verification
        self.assertTrue(user.check_password('testpass'))
        self.assertFalse(user.check_password('wrongpass'))
        
        # Test PIN verification
        self.assertTrue(user.check_pin('1234'))
        self.assertFalse(user.check_pin('0000'))


if __name__ == '__main__':
    unittest.main()
