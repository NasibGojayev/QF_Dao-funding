"""
Database seed data for testing and development
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Project, Round, Grant
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Seed database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create users
        users = self.create_users()
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))

        # Create rounds
        rounds = self.create_rounds()
        self.stdout.write(self.style.SUCCESS(f'Created {len(rounds)} rounds'))

        # Create projects
        projects = self.create_projects(users)
        self.stdout.write(self.style.SUCCESS(f'Created {len(projects)} projects'))

        # Create grants
        grants = self.create_grants(projects)
        self.stdout.write(self.style.SUCCESS(f'Created {len(grants)} grants'))

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    def create_users(self):
        users = []
        usernames = ['alice', 'bob', 'charlie', 'diana', 'eve']
        
        for username in usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': username.capitalize(),
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        return users

    def create_rounds(self):
        rounds = []
        round_data = [
            {
                'name': 'Spring 2025 Round',
                'start_at': datetime.now() - timedelta(days=30),
                'end_at': datetime.now() + timedelta(days=30),
            },
            {
                'name': 'Summer 2025 Round',
                'start_at': datetime.now() + timedelta(days=60),
                'end_at': datetime.now() + timedelta(days=120),
            },
            {
                'name': 'Fall 2025 Round',
                'start_at': datetime.now() + timedelta(days=150),
                'end_at': datetime.now() + timedelta(days=210),
            },
        ]

        for data in round_data:
            round_obj, _ = Round.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            rounds.append(round_obj)

        return rounds

    def create_projects(self, users):
        projects = []
        project_data = [
            {
                'title': 'Open Source Library Development',
                'description': 'Building a comprehensive open-source library for Web3 developers to accelerate dApp development.',
                'metadata_uri': 'ipfs://QmOpenSourceLib123',
            },
            {
                'title': 'Community Education Platform',
                'description': 'Free educational resources and tutorials for learning blockchain development and smart contract security.',
                'metadata_uri': 'ipfs://QmEducationPlatform456',
            },
            {
                'title': 'Environmental Impact Tracker',
                'description': 'Blockchain-based platform to track and verify carbon offset projects and environmental initiatives.',
                'metadata_uri': 'ipfs://QmEnviroTracker789',
            },
            {
                'title': 'Decentralized Identity Solution',
                'description': 'Privacy-preserving identity verification system for Web3 applications.',
                'metadata_uri': 'ipfs://QmIdentitySolution012',
            },
            {
                'title': 'Public Goods Funding Research',
                'description': 'Academic research into optimal mechanisms for funding public goods in decentralized ecosystems.',
                'metadata_uri': 'ipfs://QmResearch345',
            },
            {
                'title': 'Developer Tools Suite',
                'description': 'Comprehensive toolkit for smart contract testing, deployment, and monitoring.',
                'metadata_uri': 'ipfs://QmDevTools678',
            },
            {
                'title': 'Community Governance Framework',
                'description': 'Open-source governance framework for DAOs with built-in voting and proposal systems.',
                'metadata_uri': 'ipfs://QmGovernance901',
            },
            {
                'title': 'Blockchain for Social Good',
                'description': 'Using blockchain technology to solve social issues like supply chain transparency and fair trade.',
                'metadata_uri': 'ipfs://QmSocialGood234',
            },
        ]

        for i, data in enumerate(project_data):
            owner = users[i % len(users)]
            project, _ = Project.objects.get_or_create(
                title=data['title'],
                defaults={
                    **data,
                    'owner': owner,
                }
            )
            projects.append(project)

        return projects

    def create_grants(self, projects):
        grants = []
        
        for project in projects:
            # Create 1-3 grants per project
            num_grants = random.randint(1, 3)
            
            for i in range(num_grants):
                amount = random.choice([1000, 2500, 5000, 10000, 25000])
                grant, _ = Grant.objects.get_or_create(
                    project=project,
                    amount_requested=amount,
                )
                grants.append(grant)

        return grants
