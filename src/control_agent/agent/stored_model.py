from control_toolbox.storage import InMemoryDataStorage, StoredRepresentation, ReprStore
from control_toolbox.core import DataModel, DataModelTeaser
from typing import Optional
import uuid

StoredModel = StoredRepresentation[DataModel, DataModelTeaser] # type: ignore
ModelStore = ReprStore[DataModel, DataModelTeaser]
Storage = InMemoryDataStorage[DataModel]

def get_repr_store() -> ModelStore:
    storage = Storage(model_type=DataModel)
    def convert(data: DataModel, id: Optional[str]) -> StoredModel:
        return StoredModel(
            repr_id=id or str(uuid.uuid4()),
            kind=DataModel,
            content=data.to_teaser()
    )
    
    repr_store = ModelStore(storage, DataModel, DataModelTeaser, convert)
    return repr_store