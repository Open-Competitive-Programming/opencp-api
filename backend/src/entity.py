"""
The Entity class is a base class for all API entities. The main responsibility
of the Entity class is to provide a common interface for interacting via the
Open-CP API. The class defines a set of operations that can be performed
on an entity, such as listing, fetching, creating, updating, and deleting.
The specific implementation of these operations is left to the subclasses.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Type
from backend.redis import REDIS
from backend.elastic import ELASTIC_CLIENT
from backend.postgres import Base
from backend.minio import MINIO_CLIENT
from pathlib import Path
from minio.error import S3Error
from io import BytesIO
from datetime import datetime
from utils import is_valid_uuid
from config import config
import uuid
from exceptions import (
    NotAllowedError,
    DataError,
    InternalError,
    NotFoundError,
    ConflictError,
)
import logging
logger = logging.getLogger(__name__)

class Entity:
    """
    Base class for all API entities.

    In ReST terminology, an entity is a resource that can be accessed via an API.

    This class provides the basic structure for all entities. It defines the common
    operations that can be performed on an entity, such as listing, fetching, creating,
    updating, and deleting. The specific implementation of these operations is left to
    the subclasses.

    The API defined in this class is the one used by the endpoint definitions.
    """

    OPERATIONS = set(
        [
            "list",
            "fetch",
            "get",
            "create",
            "delete",
            "search",
            "patch",
        ]
    )

    def __init__(
        self,
        name: str,
        collection_name: str,
        orm_class: Type[Base], # type: ignore
        dump_schema: BaseModel,
        creation_schema: BaseModel,
        update_schema: BaseModel,
    ):
        """
        Initialize the entity with its name, collection name, creation schema, update schema, 
        and a copy of the SQLAlchemy base class.

        :param name: The name of the entity.
        :param collection_name: The name of the collection of such entities.
        :param orm_class: The ORM class representing the entity in the database.
        :param dump_schema: The schema used for dumping instances of this entity.
        :param creation_schema: The schema used for creating instances of this entity.
        :param update_schema: The schema used for updating instances of this entity.
        :param sqlalchemy_base: The SQLAlchemy base class for the entity.
        """
        self.name = name
        self.collection_name = collection_name
        self.orm_class = orm_class
        self.dump_schema = dump_schema
        self.creation_schema = creation_schema
        self.update_schema = update_schema

        self.operations = Entity.OPERATIONS.copy()
        if update_schema is None:
            self.operations.remove("patch")

    def fetch_entities(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch a list of entities bundler method.

        :param limit: The maximum number of entities to return.
        :param offset: The number of entities to skip before starting to collect the result set.
        :return: A list of entities.
        """
        return self.fetch(limit=limit, offset=offset)

    def fetch(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch a list of entities.

        :param limit: The maximum number of entities to return.
        :param offset: The number of entities to skip before starting to collect the result set.
        :return: A list of entities.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )

    def list_entities(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[str]:
        """
        List entities by their IDs bundler method.

        :param limit: The maximum number of entities to return.
        :param offset: The number of entities to skip before starting to collect the result set.
        :return: A list of IDs.
        """
        return self.list(limit=limit, offset=offset)

    def list(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[str]:
        """
        List entities by their IDs.

        :param limit: The maximum number of entities to return.
        :param offset: The number of entities to skip before starting to collect the result set.
        :return: A list of IDs.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )

    @staticmethod
    def resolve_type(entity_id: str) -> str:
        """
        Resolve the type of an entity given its ID.

        :param entity_id: The ID of the entity.
        :return: The type of the entity.
        """
        try:
            return entity_id.split(":")[1]
        except Exception as e:
            raise DataError(f"Invalid ID format: {entity_id}. Error: {e}")

    @staticmethod
    def validate_existence(entity_id: str) -> None:
        """
        Validate the existence of an entity given its ID.

        :param entity_id: The ID of the entity.
        :return: True if the entity exists, False otherwise.
        """
        entity_type = Entity.resolve_type(entity_id)
        if entity_type == "guide":
            if ELASTIC_CLIENT.get_entity(index_name="guides", id=entity_id) is None:
                raise NotFoundError(f"Guide with ID {entity_id} not found.")
        elif entity_type == "artifact":
            if ELASTIC_CLIENT.get_entity(index_name="artifacts", id=entity_id) is None:
                raise NotFoundError(f"Artifact with ID {entity_id} not found.")

    def get_identifier(self, identifier: str) -> str:
        """
        Get the ID of an entity given its ID or UUID.

        :param identifier: The ID or UUID of the entity.
        :return: The ID of the entity.
        """
        if is_valid_uuid(identifier):
            return identifier
        else:
            return identifier

    def cache(self, entity_id: str, obj) -> None:
        """
        Cache the entity.

        This method caches the entity for faster access.
        """
        if config.settings.get("CACHE_ENABLED", False):
            try:
                REDIS.set(entity_id, obj)
            except Exception as e:
                logging.error(f"Failed to cache entity {entity_id}: {e}")
    
    def invalidate_cache(self, entity_id: str) -> None:
        """
        Invalidate the cache for the entity.

        :param entity_id: The ID of the entity.
        """
        if config.settings.get("CACHE_ENABLED", False):
            try:
                REDIS.delete(entity_id)
            except Exception as e:
                logging.error(f"Failed to invalidate cache for entity {entity_id}: {e}")

    def resolve_id(self, uuid: str) -> str:
        """
        Resolve the ID of an entity given its UUID.
        :param uuid: The UUID of the entity.
        :return: The ID of the entity.
        """
        try:
            qspec = {"query": {"term": {"id": uuid}}}
            entity = ELASTIC_CLIENT.search_entities(
                index_name=self.collection_name, qspec=qspec
            )
            if not entity:
                raise NotFoundError(f"Guide with UUID {uuid} not found.")
            return entity[0]["id"]
        except Exception as e:
            raise NotFoundError(f"Failed to resolve ID for UUID {uuid}: {e}")

    def get_cached(self, entity_id: str) -> Optional[Dict[str, Any]]:
        obj = None
        if config.settings.get("CACHE_ENABLED", False):
            try:
                obj = REDIS.get(entity_id)
            except Exception as e:
                logging.error(f"Failed to get cached entity {entity_id}: {e}")

        if obj is None:
            obj = self.get(entity_id)
            self.cache(entity_id, obj)

        return self.dump_schema.model_validate(obj).model_dump(mode="json")

    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Get an entity by its ID or UUID bundler method.

        :param entity_id: The ID or UUID of the entity to fetch.
        :return: The entity or None if not found.
        """
        identifier = self.get_identifier(entity_id)
        return self.get_cached(identifier)

    async def aget_cached(self, entity_id: str) -> Dict[str, Any]:
        obj = None
        if config.settings.get("CACHE_ENABLED", False):
            try:
                obj = REDIS.get(entity_id) 
            except Exception as e:
                logging.error(f"Failed to get cached entity {entity_id}: {e}")

        if obj is None:
            obj = await self.get(entity_id) 
            self.cache(entity_id, obj)

        return self.dump_schema.model_validate(obj).model_dump(mode="json")

    async def aget_entity(self, entity_id: str) -> Dict[str, Any]:
        identifier = self.get_identifier(entity_id)
        return await self.aget_cached(identifier)

    def get(self, entity_id: str) -> Dict[str, Any]:
        """
        Get an entity by its ID or UUID.

        :param entity_id: The ID of the entity to fetch.
        :return: The entity or None if not found.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )

    def create_entity(self, spec, creator) -> Dict[str, Any]:
        """
        Create a new entity bundler method.

        :param spec: The data for the new entity.
        :param creator: The dict of the creator user fetched from header.
        :return: The created entity.
        """
        self.create(spec, creator)
        return self.get_entity(spec.get("id"))
    
    async def acreate_entity(self, spec, creator) -> Dict[str, Any]:
        """
        Create a new entity bundler method.

        :param spec: The data for the new entity.
        :param creator: The dict of the creator user fetched from header.
        :return: The created entity.
        """
        spec = await self.create(spec, creator)
        return await self.aget_entity(spec.get("id"))

    def create(self, spec, creator) -> None:
        """
        Create a new entity.

        :param data: The validated data for the new entity.
        :param creator: The creator user dict fetched from header.
        :return: The created entity.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )

    def delete_entity(self, entity_id: str) -> bool:
        """
        Delete an entity by its ID or UUID bundler method.

        :param entity_id: The ID or UUID of the entity to delete.
        :return: True if the entity was deleted, False otherwise.
        """
        identifier = self.get_identifier(entity_id)
        self.invalidate_cache(identifier)
        return self.delete(identifier)

    def delete(self, entity_id: str, purge=False) -> bool:
        """
        Delete an entity by its ID.

        :param entity_id: The ID of the entity to delete.
        :param purge: Whether to permanently delete the entity.
        :return: True if the entity was deleted, False otherwise.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )

    def patch_entity(self, entity_id: str, spec) -> Dict[str, Any]:
        """
        Update an entity by its ID or UUID bundler method.

        :param entity_id: The ID or UUID of the entity to update.
        :param data: The data to update the entity with.
        :return: The updated entity.
        """
        if self.update_schema is None:
            raise NotAllowedError(f"The {self.name} entity does not support updates.")

        identifier = self.get_identifier(entity_id)
        self.invalidate_cache(identifier)
        self.patch(identifier, spec)
        return self.get_entity(identifier)

    def patch(self, entity_id: str, spec) -> None:
        """
        Update an entity by its ID.

        :param entity_id: The ID of the entity to update.
        :param data: The validated data to update the entity with.
        :return: The updated entity.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )

    def search_entities(
        self,
        query: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Search for entities bundler method.

        :param query: The search query.
        :param limit: The maximum number of entities to return.
        :param offset: The number of entities to skip before starting to collect the result set.
        :return: A list of entities matching the search query.
        """
        return self.search(query=query)

    def search(
        self,
        query: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Search for entities.

        :param query: The search query.
        :param limit: The maximum number of entities to return.
        :param offset: The number of entities to skip before starting to collect the result set.
        :return: A list of entities matching the search query.
        """
        raise NotImplementedError(
            "Subclasses of the Entity class must implement this method."
        )
    
    def upsert_system_fields(self, spec: Dict, update=False) -> Dict[str, Any]:
        """
        Upsert system fields for the entity.

        :param data: The data to upsert system fields into.
        :return: The data with upserted system fields.
        """
        # Generate ID if not present
        if not update and "id" not in spec:
            spec["id"] = str(uuid.uuid4())

        if update and "creator" in spec:
            spec.pop("creator")
        
        # Generate timestamps
        spec["updated_at"] = str(datetime.now().isoformat())
        if not update:
            spec["created_at"] = str(datetime.now().isoformat())
        return spec