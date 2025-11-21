"""
Pydantic schemas for API request/response validation (no forward refs)
- No `from __future__ import annotations`
- Define classes in dependency order (profile -> member -> household)
- No `.model_rebuild()` calls needed
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ------- System Schemas -------
class SearchSchema(BaseModel):
    q: Optional[str] = Field(default=None, description="Search query string")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip for pagination")
    fl: Optional[List[str]] = Field(default=None, description="List of fields to include in the response")
    fq: Optional[List[str]] = Field(default=None, description="List of filter queries (e.g., 'status:active')")
    sort: Optional[str] = Field(default=None, description="Sort order (e.g., 'created_at desc')")
    fields: Optional[List[str]] = Field(default=None, description="List of fields to aggregate for faceting")

class LoginSchema(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
