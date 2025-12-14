"""Seed script to load sample data for Sprint 2 local development.

Run: python seed_db.py
"""
from db import create_tables, engine
from models import Base, User, Project, Transaction, Tag, Milestone
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


def seed():
    create_tables(Base)
    with Session(bind=engine) as s:
        # create users
        u1 = User(wallet='0x' + '1'*40, email='alice@example.com')
        u2 = User(wallet='0x' + '2'*40, email='bob@example.com')
        s.add_all([u1, u2])
        s.flush()

        p1 = Project(owner_id=u1.id, title='Community Garden', description='Plant trees')
        p2 = Project(owner_id=u2.id, title='Open Source Library', description='Build SDK')
        s.add_all([p1, p2])
        s.flush()

        t1 = Tag(name='environment')
        t2 = Tag(name='infrastructure')
        s.add_all([t1, t2])
        s.flush()

        s.add_all([
            Transaction(tx_hash='0xtx1', user_id=u1.id, project_id=p1.id, amount=10.0, created_at=datetime.utcnow()-timedelta(days=2)),
            Transaction(tx_hash='0xtx2', user_id=u2.id, project_id=p2.id, amount=25.0, created_at=datetime.utcnow()-timedelta(days=1)),
        ])

        s.add_all([
            Milestone(project_id=p1.id, title='Phase 1'),
            Milestone(project_id=p2.id, title='MVP Release'),
        ])

        s.commit()
    print('Seeded sample data')


if __name__ == '__main__':
    seed()
