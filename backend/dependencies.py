from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.db.database import get_db_session

logger = get_logger(__name__)


SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[AsyncSession, Depends(get_db_session)]