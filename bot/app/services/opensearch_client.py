"""OpenSearch client for barcode card storage."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from opensearchpy import OpenSearch, NotFoundError

logger = logging.getLogger(__name__)

INDEX_NAME = "barcode_cards"

INDEX_BODY = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "owner_id": {"type": "long"},
            "card_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "card_code": {"type": "keyword"},
            "barcode_format": {"type": "keyword"},
            "created_at": {"type": "date"},
        }
    },
}


class OpenSearchClient:
    """Thin wrapper around the OpenSearch Python client."""

    def __init__(self, host: str, port: int) -> None:
        self.client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            timeout=30,
        )

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def wait_for_cluster(self, retries: int = 30, delay: float = 2.0) -> None:
        """Block until the cluster is reachable."""
        for attempt in range(retries):
            try:
                info = self.client.info()
                logger.info("Connected to OpenSearch %s", info["version"]["number"])
                return
            except Exception:
                logger.warning(
                    "OpenSearch not ready (attempt %d/%d), retrying in %.0fs …",
                    attempt + 1,
                    retries,
                    delay,
                )
                time.sleep(delay)
        raise RuntimeError("Could not connect to OpenSearch")

    def init_index(self) -> None:
        """Create the card index if it does not exist.

        If an older index exists with ``user_id`` instead of ``owner_id``,
        delete and re-create it (data migration for the schema change).
        """
        if self.client.indices.exists(INDEX_NAME):
            mapping = self.client.indices.get_mapping(INDEX_NAME)
            props = mapping[INDEX_NAME]["mappings"].get("properties", {})
            if "owner_id" not in props:
                logger.info(
                    "Index '%s' has old schema (user_id) — recreating with owner_id",
                    INDEX_NAME,
                )
                self.client.indices.delete(INDEX_NAME)
                self.client.indices.create(INDEX_NAME, body=INDEX_BODY)
                logger.info("Recreated index '%s' with owner_id schema", INDEX_NAME)
            else:
                logger.info("Index '%s' already exists", INDEX_NAME)
        else:
            self.client.indices.create(INDEX_NAME, body=INDEX_BODY)
            logger.info("Created index '%s'", INDEX_NAME)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_card(
        self,
        owner_id: int,
        card_name: str,
        card_code: str,
        barcode_format: str,
    ) -> str:
        """Store a card and return its document id.

        *owner_id* is the user id in private chats or the chat id in groups.
        """
        doc = {
            "owner_id": owner_id,
            "card_name": card_name,
            "card_code": card_code,
            "barcode_format": barcode_format,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        resp = self.client.index(index=INDEX_NAME, body=doc, refresh="wait_for")
        return resp["_id"]

    def get_cards(self, owner_id: int) -> list[dict]:
        """Return all cards belonging to *owner_id*, sorted by creation date."""
        body = {
            "query": {"term": {"owner_id": owner_id}},
            "sort": [{"created_at": {"order": "asc"}}],
            "size": 100,
        }
        resp = self.client.search(index=INDEX_NAME, body=body)
        return [{"id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]

    def get_card(self, card_id: str) -> dict | None:
        """Fetch a single card by id, or *None* if missing."""
        try:
            resp = self.client.get(index=INDEX_NAME, id=card_id)
            return {"id": resp["_id"], **resp["_source"]}
        except NotFoundError:
            return None

    def delete_card(self, card_id: str, owner_id: int) -> bool:
        """Delete a card only if it belongs to *owner_id*."""
        card = self.get_card(card_id)
        if card and card["owner_id"] == owner_id:
            self.client.delete(index=INDEX_NAME, id=card_id, refresh="wait_for")
            return True
        return False

    def search_cards(self, owner_id: int, query_text: str) -> list[dict]:
        """Full-text search over card names for a given owner."""
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"owner_id": owner_id}},
                        {"match": {"card_name": query_text}},
                    ]
                }
            },
            "size": 20,
        }
        resp = self.client.search(index=INDEX_NAME, body=body)
        return [{"id": h["_id"], **h["_source"]} for h in resp["hits"]["hits"]]
