"""
Backend API Tests for Django REST Framework
Tests all endpoints: Projects, Rounds, Grants
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from api.models import Project, Round, Grant
from datetime import datetime, timedelta


class ProjectAPITests(TestCase):
    """Test suite for Project API endpoints"""
    
    def setUp(self):
        """Set up test client and authentication"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_list_projects_requires_auth(self):
        """Test that listing projects requires authentication"""
        client = APIClient()  # Unauthenticated client
        response = client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_projects_authenticated(self):
        """Test listing projects with authentication"""
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_project(self):
        """Test creating a new project"""
        data = {
            'title': 'Test Project',
            'description': 'A test project description',
            'metadata_uri': 'ipfs://QmTest123'
        }
        response = self.client.post('/api/projects/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().title, 'Test Project')
    
    def test_create_project_sets_owner(self):
        """Test that creating a project sets the current user as owner"""
        data = {
            'title': 'Test Project',
            'description': 'Description',
            'metadata_uri': 'ipfs://QmTest'
        }
        self.client.post('/api/projects/', data, format='json')
        project = Project.objects.get()
        self.assertEqual(project.owner, self.user)
    
    def test_retrieve_project(self):
        """Test retrieving a specific project"""
        project = Project.objects.create(
            title='Test Project',
            description='Description',
            owner=self.user,
            metadata_uri='ipfs://QmTest'
        )
        response = self.client.get(f'/api/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Project')
    
    def test_update_project(self):
        """Test updating a project"""
        project = Project.objects.create(
            title='Original Title',
            description='Description',
            owner=self.user
        )
        data = {'title': 'Updated Title'}
        response = self.client.patch(f'/api/projects/{project.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.title, 'Updated Title')
    
    def test_delete_project(self):
        """Test deleting a project"""
        project = Project.objects.create(
            title='Test Project',
            owner=self.user
        )
        response = self.client.delete(f'/api/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)
    
    def test_list_projects_ordered_by_created_at(self):
        """Test that projects are ordered by creation date (newest first)"""
        Project.objects.create(title='Project 1', owner=self.user)
        Project.objects.create(title='Project 2', owner=self.user)

        response = self.client.get('/api/projects/')
        self.assertEqual(response.data[0]['title'], 'Project 2')
        self.assertEqual(response.data[1]['title'], 'Project 1')


class RoundAPITests(TestCase):
    """Test suite for Round API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_list_rounds_requires_auth(self):
        """Test that listing rounds requires authentication"""
        client = APIClient()
        response = client.get('/api/rounds/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_round(self):
        """Test creating a new round"""
        now = datetime.now()
        data = {
            'name': 'Test Round',
            'start_at': now.isoformat(),
            'end_at': (now + timedelta(days=30)).isoformat()
        }
        response = self.client.post('/api/rounds/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Round.objects.count(), 1)
    
    def test_retrieve_round(self):
        """Test retrieving a specific round"""
        round_obj = Round.objects.create(
            name='Test Round',
            start_at=datetime.now(),
            end_at=datetime.now() + timedelta(days=30)
        )
        response = self.client.get(f'/api/rounds/{round_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Round')


class GrantAPITests(TestCase):
    """Test suite for Grant API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user
        )
    
    def test_list_grants_requires_auth(self):
        """Test that listing grants requires authentication"""
        client = APIClient()
        response = client.get('/api/grants/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_grant(self):
        """Test creating a new grant"""
        data = {
            'project': self.project.id,
            'amount_requested': '1000.50'
        }
        response = self.client.post('/api/grants/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Grant.objects.count(), 1)
    
    def test_retrieve_grant(self):
        """Test retrieving a specific grant"""
        grant = Grant.objects.create(
            project=self.project,
            amount_requested=1000.50
        )
        response = self.client.get(f'/api/grants/{grant.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['amount_requested']), 1000.50)


class AuthenticationTests(TestCase):
    """Test suite for authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_obtain_auth_token(self):
        """Test obtaining authentication token"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api-token-auth/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
    
    def test_invalid_credentials(self):
        """Test authentication with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api-token-auth/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_api_requires_token(self):
        """Test that API endpoints require token"""
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_api_with_valid_token(self):
        """Test API access with valid token"""
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaginationTests(TestCase):
    """Test suite for pagination"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create 60 projects (more than page size of 50)
        for i in range(60):
            Project.objects.create(
                title=f'Project {i}',
                owner=self.user
            )
    
    def test_pagination_applied(self):
        """Test that pagination is applied"""
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 60)
        self.assertEqual(len(response.data['results']), 50)  # Page size
    
    def test_pagination_next_page(self):
        """Test accessing next page"""
        response = self.client.get('/api/projects/?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Remaining items
