import threading
from elasticsearch import Elasticsearch
from config import config
from schemas import SearchSchema

class ElasticsearchClientSingleton:
    """Singleton class that holds a pool of Elasticsearch clients."""

    _pool = []
    _counter = 0
    _lock = threading.Lock()

    def get_client(self) -> Elasticsearch:
        """Ensure pool is initialized and return one Elasticsearch client (round robin)."""
        if not self._pool:
            self._initialize_elasticsearch()
        pool_item = self._select_pool_item()
        return pool_item

    @classmethod
    def _select_pool_item(cls):
        with cls._lock:
            index = cls._counter % len(cls._pool)
            cls._counter += 1
            return cls._pool[index]

    @classmethod
    def _bootstrap(cls):
        """Create indices in Elasticsearch if they do not exist."""
        es = Elasticsearch(hosts=config.settings["ELASTIC_HOST"])
       

    @classmethod
    def _initialize_elasticsearch(cls):
        """Initialize a pool of Elasticsearch clients."""
        pool_size = int(config.settings.get("ELASTICSEARCH_POOL_SIZE", 5))
        for _ in range(pool_size):
            client = Elasticsearch(hosts=config.settings["ELASTIC_HOST"])
            cls._pool.append(client)
        cls._bootstrap()

    def index_exists(self, index_name: str) -> bool:
        client = self.get_client()
        return client.indices.exists(index=index_name)

    def get_entity(self, index_name: str, urn: str):
        client = self.get_client()
        try:
            r = client.get(index=index_name, id=urn)
            return r["_source"]
        except Exception:
            return None

    def list_entities(
        self, index_name: str, size: int = 1000, offset: int = 0
    ) -> list[str]:
        client = self.get_client()
        body = {
            "from": offset,
            "size": size,
            "_source": False,
            "query": {"bool": {"must_not": {"term": {"status": "deleted"}}}},
        }
        r = client.search(index=index_name, body=body, _source_includes=["_id"])
        return [h["_id"] for h in r["hits"]["hits"]]

    def fetch_entities(self, index_name: str, limit: int, offset: int) -> list[dict]:
        """
        Fetch entity representations from an Elasticsearch index
        using offset + limit pagination.

        Args:
            index_name: name of the ES index
            limit: number of entities to return
            offset: starting offset for pagination

        Returns:
            List of entity documents (_source only).
        """
        client = self.get_client()
        body = {
            "from": offset,
            "size": limit,
            "query": {"bool": {"must_not": {"term": {"status": "deleted"}}}},
        }
        r = client.search(
            index=index_name,
            body=body,
        )
        return [hit["_source"] for hit in r["hits"]["hits"]]

    def index_entity(self, index_name: str, document: dict):
        client = self.get_client()
        client.index(
            index=index_name, id=document.get("urn", document.get("id")), document=document, refresh="wait_for"
        )

    def delete_entity(self, index_name: str, urn: str):
        client = self.get_client()
        client.delete(index=index_name, id=urn, refresh="wait_for")

    def update_entity(self, index_name: str, document: dict):
        client = self.get_client()
        client.update(
            index=index_name, id=document["urn"], doc=document, refresh="wait_for"
        )

    def search_entities(self, index_name: str, qspec: SearchSchema):
        client = self.get_client()
        if "offset" not in qspec or qspec.get("offset") is None:
            qspec["offset"] = 0
        if "limit" not in qspec or qspec.get("limit") is None:
            qspec["limit"] = 100

        body = {
            "from": qspec.get("offset"),
            "size": qspec.get("limit"),
            "query": {
                "bool": {
                    "must": [{"multi_match": {"query": qspec.get("q"), "fields": ["*"]}}] if qspec.get("q") else [],
                    "filter": [{"query_string": {"query": fq}} for fq in qspec.get("fq", [])] if qspec.get("fq") else [],
                }
            },
        }

        # Determine which fields to aggregate on
        facet_fields = qspec.get("facet_fields", [])
        
        # If no facet_fields specified, extract fields from fq filters
        if not facet_fields and qspec.get("fq"):
            extracted_fields = set()
            for fq in qspec.get("fq"):
                # Extract field name from filter queries like "tags:wellness" or "category:health"
                if ":" in fq:
                    field_name = fq.split(":")[0].strip()
                    extracted_fields.add(field_name)
            facet_fields = list(extracted_fields)

        # Add aggregations for faceting
        if facet_fields:
            body["aggs"] = {}
            for facet_field in facet_fields:
                # Try the field as-is first (for keyword type fields)
                body["aggs"][f"{facet_field}_facet"] = {
                    "terms": {
                        "field": facet_field,
                        "size": qspec.get("facet_limit", 50)
                    }
                }

        if qspec.get("fl"):
            source_fields = []
            source_includes = {}
            for field in qspec.get("fl"):
                if ":" in field:
                    original_field, alias = field.split(":")
                    source_fields.append(original_field)
                    source_includes[original_field] = alias
                else:
                    source_fields.append(field)
            body["_source"] = source_fields

        if qspec.get("sort"):
            sort_field, sort_order = qspec.get("sort").split() if " " in qspec.get("sort") else (qspec.get("sort"), "asc")
            body["sort"] = [{sort_field: {"order": sort_order}}]

        try:
            r = client.search(index=index_name, body=body)
        except Exception as e:
            # If aggregation fails, try with .keyword suffix
            if facet_fields and "aggs" in body:
                body["aggs"] = {}
                for facet_field in facet_fields:
                    body["aggs"][f"{facet_field}_facet"] = {
                        "terms": {
                            "field": f"{facet_field}.keyword",
                            "size": qspec.get("facet_limit", 50)
                        }
                    }
                r = client.search(index=index_name, body=body)
            else:
                raise e
        
        # Process results
        results = []
        for hit in r["hits"]["hits"]:
            source = hit["_source"]
            if qspec.get("fl"):
                aliased_source = {}
                for field in qspec.get("fl"):
                    if ":" in field:
                        original_field, alias = field.split(":")
                        if original_field in source:
                            aliased_source[alias] = source[original_field]
                    else:
                        if field in source:
                            aliased_source[field] = source[field]
                results.append(aliased_source)
            else:
                results.append(source)
        
        # Extract facet counts
        facets = {}
        if "aggregations" in r:
            for agg_name, agg_data in r["aggregations"].items():
                field_name = agg_name.replace("_facet", "")
                facets[field_name] = [
                    {"value": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in agg_data["buckets"]
                ]
        
        return {"results": results, "facets": facets, "total": r["hits"]["total"]["value"]}

ELASTIC_CLIENT = ElasticsearchClientSingleton()