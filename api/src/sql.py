"""
SQLAlchemy models and database access methods for Open-CP API
"""
from __future__ import annotations
from sqlalchemy import inspect as sa_inspect
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
import enum

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Table,
    Text,
    Index,
    select,
    delete,
    Enum,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from backend.postgres import Base