import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

load_dotenv(dotenv_path=API_ROOT.parents[1] / ".env")


@pytest.fixture
def mock_db_pool():
    pool = MagicMock()
    conn = AsyncMock()

    class AcquireCtx:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, *args):
            return None

    pool.acquire.return_value = AcquireCtx()
    return pool, conn
