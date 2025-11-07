from __future__ import annotations

from typing import Any, Tuple, get_args, get_origin, Annotated

def _unwrap_annotated(t: Any) -> Any:
    """Return the underlying type if t is Annotated[T, ...]."""
    if get_origin(t) is Annotated:
        return get_args(t)[0]
    return t

def dataset_types(dataset: Any) -> Tuple[type[Any], type[Any], type[Any]]:
    """
    Return (InputT, OutputT, MetadataT) for a parameterized Dataset[...] instance.

    Works when the class actually subclasses typing.Generic and the instance
    was created as Dataset[In, Out, Meta](...).
    """
    oc = getattr(dataset, "__orig_class__", None)
    if oc is None:
        # Helpful message for common pitfalls
        raise TypeError(
            "Dataset instance has no __orig_class__. "
            "Make sure you constructed it as Dataset[In, Out, Meta](...) "
            "instead of just Dataset(...)."
        )

    args = tuple(_unwrap_annotated(a) for a in get_args(oc))
    if len(args) != 3:
        raise TypeError(f"Expected 3 generic args on Dataset, got {len(args)}: {args}")

    InT, OutT, MetaT = args  # type: ignore[assignment]
    # Optionally resolve forward refs that slipped through as strings
    if isinstance(InT, str) or isinstance(OutT, str) or isinstance(MetaT, str):
        # Best-effort: eval against the module where the dataset instance's class lives
        ns = getattr(type(dataset), "__dict__", {})
        globs = getattr(type(dataset), "__globals__", {}) if hasattr(type(dataset), "__globals__") else {}
        InT = eval(InT, globs, ns) if isinstance(InT, str) else InT
        OutT = eval(OutT, globs, ns) if isinstance(OutT, str) else OutT
        MetaT = eval(MetaT, globs, ns) if isinstance(MetaT, str) else MetaT

    return InT, OutT, MetaT  # type: ignore[return-value]