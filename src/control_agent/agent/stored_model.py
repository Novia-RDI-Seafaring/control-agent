from pydantic import BaseModel, Field
from typing import TypeVar, Generic
from uuid import uuid4

# Type variables for the StoredModel class
T = TypeVar("T", bound=BaseModel)

class TypedStore(BaseModel):
    buckets: dict[str, dict[str, BaseModel]] = Field(default_factory=dict)

    def add(self, model: BaseModel, *, kind: str | None = None) -> tuple[str, str]:
        k = kind or model.__class__.__name__
        rid = uuid4().hex
        self.buckets.setdefault(k, {})[rid] = model
        return k, rid

    def get(self, kind: str, rid: str) -> BaseModel:
        return self.buckets[kind][rid]

class StoredModel(BaseModel, Generic[T]):   # <- no GenericModel needed
    kind: str
    id: str

    @classmethod
    def store(cls, store: TypedStore, model: T, *, kind: str | None = None) -> "StoredModel[T]":
        k, rid = store.add(model, kind=kind)
        return cls(kind=k, id=rid)

    def is_of(self, model: type[BaseModel]) -> bool:
        return self.kind == model.__name__

    def resolve(self, store: TypedStore) -> T:
        return store.get(self.kind, self.id)  # type: ignore[return-value]


