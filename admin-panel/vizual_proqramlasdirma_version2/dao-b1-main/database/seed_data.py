"""
Seed Data Script for DAO Database

Populates the database with sample data for development and testing.
Usage: python seed_data.py
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_session, engine
from models import Base, User, Project, Tag, Transaction, Milestone, ProjectTag, IndexerState


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")


def seed_users(session):
    """Create sample users."""
    users = [
        User(wallet="0x1111111111111111111111111111111111111111", email="alice@example.com", is_admin=True),
        User(wallet="0x2222222222222222222222222222222222222222", email="bob@example.com", is_admin=False),
        User(wallet="0x3333333333333333333333333333333333333333", email="carol@example.com", is_admin=False),
        User(wallet="0x4444444444444444444444444444444444444444", email="dave@example.com", is_admin=False),
        User(wallet="0x5555555555555555555555555555555555555555", email="eve@example.com", is_admin=False),
    ]
    session.add_all(users)
    session.flush()
    print(f"✓ Created {len(users)} users")
    return users


def seed_tags(session):
    """Create sample tags."""
    tags = [
        Tag(name="environment"),
        Tag(name="education"),
        Tag(name="infrastructure"),
        Tag(name="healthcare"),
        Tag(name="technology"),
        Tag(name="community"),
        Tag(name="arts"),
    ]
    session.add_all(tags)
    session.flush()
    print(f"✓ Created {len(tags)} tags")
    return tags


def seed_projects(session, users, tags):
    """Create sample projects with milestones and tags."""
    projects = [
        Project(
            owner_id=users[0].id,
            title="Community Garden Initiative",
            description="Creating green spaces in urban areas for community use.",
            is_active=True
        ),
        Project(
            owner_id=users[1].id,
            title="Open Source Education Platform",
            description="Building free educational resources for underprivileged students.",
            is_active=True
        ),
        Project(
            owner_id=users[2].id,
            title="Clean Water Access Project",
            description="Installing water purification systems in rural communities.",
            is_active=True
        ),
        Project(
            owner_id=users[0].id,
            title="Local Tech Hub",
            description="Creating a space for tech workshops and mentorship.",
            is_active=True
        ),
        Project(
            owner_id=users[3].id,
            title="Public Art Installation",
            description="Collaborative mural project for downtown beautification.",
            is_active=False
        ),
    ]
    session.add_all(projects)
    session.flush()
    print(f"✓ Created {len(projects)} projects")
    
    # Add milestones to projects
    milestones = [
        Milestone(project_id=projects[0].id, title="Phase 1: Land Acquisition", target_amount=Decimal("5.0")),
        Milestone(project_id=projects[0].id, title="Phase 2: Initial Planting", target_amount=Decimal("3.0")),
        Milestone(project_id=projects[0].id, title="Phase 3: Community Launch", target_amount=Decimal("2.0")),
        Milestone(project_id=projects[1].id, title="MVP Development", target_amount=Decimal("10.0")),
        Milestone(project_id=projects[1].id, title="Beta Launch", target_amount=Decimal("5.0")),
        Milestone(project_id=projects[2].id, title="Equipment Purchase", target_amount=Decimal("15.0")),
        Milestone(project_id=projects[2].id, title="Installation", target_amount=Decimal("8.0"), resolved=True, resolved_at=datetime.utcnow()),
    ]
    session.add_all(milestones)
    session.flush()
    print(f"✓ Created {len(milestones)} milestones")
    
    # Assign tags to projects
    project_tags = [
        ProjectTag(project_id=projects[0].id, tag_id=tags[0].id),  # Garden -> environment
        ProjectTag(project_id=projects[0].id, tag_id=tags[5].id),  # Garden -> community
        ProjectTag(project_id=projects[1].id, tag_id=tags[1].id),  # Education -> education
        ProjectTag(project_id=projects[1].id, tag_id=tags[4].id),  # Education -> technology
        ProjectTag(project_id=projects[2].id, tag_id=tags[2].id),  # Water -> infrastructure
        ProjectTag(project_id=projects[2].id, tag_id=tags[3].id),  # Water -> healthcare
        ProjectTag(project_id=projects[3].id, tag_id=tags[4].id),  # Tech Hub -> technology
        ProjectTag(project_id=projects[3].id, tag_id=tags[5].id),  # Tech Hub -> community
        ProjectTag(project_id=projects[4].id, tag_id=tags[6].id),  # Art -> arts
    ]
    session.add_all(project_tags)
    session.flush()
    print(f"✓ Created {len(project_tags)} project-tag associations")
    
    return projects


def seed_transactions(session, users, projects, tags):
    """Create sample transactions."""
    transactions = []
    base_time = datetime.utcnow() - timedelta(days=30)
    
    # Generate 50 sample transactions
    for i in range(50):
        user = random.choice(users)
        project = random.choice(projects)
        tag = random.choice(tags) if random.random() > 0.3 else None
        
        tx = Transaction(
            tx_hash=f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            block_number=1000000 + i * 100,
            user_id=user.id,
            project_id=project.id,
            tag_id=tag.id if tag else None,
            amount=Decimal(str(round(random.uniform(0.01, 10.0), 4))),
            created_at=base_time + timedelta(hours=i * 12 + random.randint(0, 11)),
            processed_at=base_time + timedelta(hours=i * 12 + random.randint(0, 11), seconds=5),
            success=random.random() > 0.05,  # 95% success rate
            event_type=random.choice(["TransactionCreated", "DonationReceived", "ContributionMade"])
        )
        transactions.append(tx)
    
    session.add_all(transactions)
    session.flush()
    print(f"✓ Created {len(transactions)} transactions")
    return transactions


def seed_indexer_state(session):
    """Initialize indexer state."""
    state = IndexerState(
        contract_address="0x0000000000000000000000000000000000000000",
        last_block_processed=1000000
    )
    session.add(state)
    session.flush()
    print("✓ Initialized indexer state")


def main():
    """Run all seed functions."""
    print("\n" + "="*50)
    print("DAO Database Seed Script")
    print("="*50 + "\n")
    
    # Create tables
    create_tables()
    
    with get_session() as session:
        # Check if data already exists
        existing_users = session.query(User).count()
        if existing_users > 0:
            print(f"\n⚠ Database already has {existing_users} users. Skipping seed.")
            print("  To reseed, run: python -c \"from config import drop_tables; drop_tables()\"")
            return
        
        # Seed in order (respecting foreign keys)
        users = seed_users(session)
        tags = seed_tags(session)
        projects = seed_projects(session, users, tags)
        seed_transactions(session, users, projects, tags)
        seed_indexer_state(session)
        
        # Commit is handled by context manager
    
    print("\n" + "="*50)
    print("✓ Seed complete!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
