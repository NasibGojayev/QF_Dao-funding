from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DB_URL

Base = declarative_base()
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

class ProposalEvent(Base):
    __tablename__ = "proposal_events"
    id = Column(Integer, primary_key=True)
    tx_hash = Column(String, unique=True)
    block_number = Column(BigInteger)
    proposal_id = Column(BigInteger)
    owner = Column(String)
    metadata_uri = Column(String)
    active = Column(Integer, default=1)  # 1 for True, 0 for False

def init_db():
    Base.metadata.create_all(engine)
