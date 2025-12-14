#!/usr/bin/env python
"""Quick DB inspection helper."""
from backend.db import SessionLocal
from backend.models import User, Project, Transaction, Tag, Milestone, ProjectTag

session = SessionLocal()
print("\n=== Database Summary ===")
print(f"Users: {session.query(User).count()}")
print(f"Projects: {session.query(Project).count()}")
print(f"Transactions: {session.query(Transaction).count()}")
print(f"Tags: {session.query(Tag).count()}")
print(f"Milestones: {session.query(Milestone).count()}")
print(f"ProjectTags: {session.query(ProjectTag).count()}")
session.close()
