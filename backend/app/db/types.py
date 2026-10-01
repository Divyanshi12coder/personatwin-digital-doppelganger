"""Dialect-aware embedding column.

* PostgreSQL -> native ``vector(n)`` from pgvector (indexed with HNSW, searched
  in SQL with the cosine-distance operator ``<=>``).
* Anything else (SQLite for tests / quick local runs) -> JSON-encoded text;
  similarity is computed in Python by ``app.services.retrieval``.
"""

import json
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Text
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


class EmbeddingVector(TypeDecorator[list[float]]):
    impl = Text
    cache_ok = True

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is None:
            return None
        values = [float(x) for x in value]
        if len(values) != self.dim:
            raise ValueError(f"Embedding has {len(values)} dimensions, expected {self.dim}")
        if dialect.name == "postgresql":
            return values
        return json.dumps(values)

    def process_result_value(self, value: Any, dialect: Dialect) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return [float(x) for x in json.loads(value)]
        return [float(x) for x in value]
