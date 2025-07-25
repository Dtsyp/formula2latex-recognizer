import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest
import pytest_postgresql

# Добавляем src в Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from infrastructure.database import Base
import infrastructure.models

postgresql_proc = pytest_postgresql.factories.postgresql_proc(
    port=None, unixsocketdir='/tmp'
)
postgresql = pytest_postgresql.factories.postgresql('postgresql_proc')

@pytest.fixture
def test_db(postgresql):
    """Create test database session"""
    connection_string = f"postgresql://postgres@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    engine = create_engine(connection_string)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up
        Base.metadata.drop_all(engine)