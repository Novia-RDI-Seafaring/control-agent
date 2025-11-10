from __future__ import annotations

from typing import Any, Tuple, get_args, get_origin, Annotated

def _unwrap_annotated(t: Any) -> Any:
    """Return the underlying type if t is Annotated[T, ...]."""
    if get_origin(t) is Annotated:
        return get_args(t)[0]
    return t