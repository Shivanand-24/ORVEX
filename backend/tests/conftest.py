import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db_session
from app.llm import LLMGateway, MockLLMProvider, get_llm_gateway

# In-memory SQLite for fast, isolated async testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(name="db_session")
async def db_session_fixture() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestSession = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with AsyncTestSession() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(name="client")
async def client_fixture(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    from app.core.config import Settings
    test_settings = Settings(LLM_PROVIDER="mock", LLM_MODEL="gpt-4o-mini")
    mock_gateway = LLMGateway(provider=MockLLMProvider(default_model="gpt-4o-mini"), settings=test_settings)
    app.dependency_overrides[get_llm_gateway] = lambda: mock_gateway
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
