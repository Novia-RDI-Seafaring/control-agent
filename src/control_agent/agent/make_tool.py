from __future__ import annotations
from typing import Any, Callable, Generic, Dict, Optional, Tuple, Type, TypeVar, Union, get_type_hints, get_origin, get_args
from functools import wraps
from inspect import signature, Parameter, Signature
from pydantic import BaseModel, Field

from pydantic_ai.tools import Tool
from pydantic_ai._run_context import RunContext
from uuid import uuid4

from control_toolbox.core import DataModel, ResponseModel
from control_toolbox.tools.simulation import SimulationProps, ImpulseProps, StepProps

TypesT = Tuple[type[BaseModel], ...]
INPUT_TYPES_DEFAULT: TypesT = (SimulationProps, ImpulseProps, StepProps, DataModel)
OUTPUT_TYPES_DEFAULT: TypesT = (ResponseModel, DataModel)


def _strip_optional(tp):
    """Return inner type for Optional[T]/Union[T, None]."""
    if get_origin(tp) is Union:
        args = tuple(a for a in get_args(tp) if a is not type(None))
        if len(args) == 1:
            return args[0]
    return tp

def _is_model_from_pool(tp, pool: TypesT) -> bool:
    """True if type annotation tp (after unwrapping Optional) is a BaseModel subclass in pool."""
    try:
        inner = _strip_optional(tp)
        return isinstance(inner, type) and issubclass(inner, BaseModel) and any(issubclass(inner, p) for p in pool)
    except Exception:
        return False

def _resolve_value(store: TypedStore, expected_tp, v: Any) -> Any:
    """Resolve StoredModel handles; recurse into common containers."""
    tp = _strip_optional(expected_tp)

    if isinstance(v, StoredModel):
        # If annotation expects a BaseModel, resolve the handle.
        if isinstance(tp, type) and issubclass(tp, BaseModel):
            return v.resolve(store)
        return v

    origin = get_origin(tp)
    args = get_args(tp)

    if origin in (list, tuple) and args and isinstance(v, (list, tuple)):
        inner_tp = args[0]
        seq = [_resolve_value(store, inner_tp, x) for x in v]
        return type(v)(seq) if isinstance(v, tuple) else seq

    if origin is dict and len(args) == 2 and isinstance(v, dict):
        key_tp, val_tp = args
        return { _resolve_value(store, key_tp, k): _resolve_value(store, val_tp, x) for k, x in v.items() }

    return v


# ---------------------------------------------
# 4) Resolver that understands handles (incl. containers)
# ---------------------------------------------

def _resolve_value(store: TypedStore, expected_tp, v: Any) -> Any:
    # If parameter is annotated as one of INPUT_TYPES and value is a StoredModel, resolve it.
    tp = _strip_optional(expected_tp)
    if isinstance(v, StoredModel):
        # If it's a handle and we *expect* a BaseModel input, resolve it.
        if isinstance(tp, type) and issubclass(tp, BaseModel):
            return v.resolve(store)
        return v  # not an expected input type; leave as-is

    # Recursively resolve inside common containers if element type looks like an input type
    origin = get_origin(tp)
    args = get_args(tp)
    if origin in (list, tuple) and args:
        inner_tp = args[0]
        if isinstance(v, (list, tuple)):
            seq = [_resolve_value(store, inner_tp, x) for x in v]
            return type(v)(seq) if isinstance(v, tuple) else seq
    if origin is dict and len(args) == 2:
        key_tp, val_tp = args
        if isinstance(v, dict):
            return { _resolve_value(store, key_tp, k): _resolve_value(store, val_tp, x) for k, x in v.items() }

    return v


F = TypeVar("F", bound=Callable[..., Any])

def wrap_as_stored_tool(
    fn: F,
    input_types: Optional[Tuple[type[BaseModel], ...] | list[type[BaseModel]]] = None,
    output_types: Optional[Tuple[type[BaseModel], ...] | list[type[BaseModel]]] = None,
) -> Callable[..., Any]:
    """
    Make a ctx-aware tool that:
      • resolves StoredModel[...] for parameters annotated with any of `input_types`
      • stores returns if they are instances of any `output_types`, and returns a StoredModel[...] handle
    """
    # Normalize pools to tuples
    in_pool: TypesT = tuple(input_types) if input_types is not None else INPUT_TYPES_DEFAULT
    out_pool: TypesT = tuple(output_types) if output_types is not None else OUTPUT_TYPES_DEFAULT

    orig_sig = signature(fn)
    orig_hints = get_type_hints(fn)

    @wraps(fn)
    def wrapped(ctx: RunContext, *args, **kwargs):
        store = ctx.deps

        # Bind to the original fn's signature (no ctx there)
        bound = orig_sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        # Resolve handles in positional/keyword args where annotation matches input pool
        for name, value in list(bound.arguments.items()):
            ann = orig_hints.get(name, orig_sig.parameters[name].annotation)
            if _is_model_from_pool(ann, in_pool):
                bound.arguments[name] = _resolve_value(store, ann, value)

        # Call pure function
        out = fn(*bound.args, **bound.kwargs)

        # Normalize return to a handle
        if isinstance(out, StoredModel):
            return out
        if isinstance(out, out_pool):
            return StoredModel.store(store, out, kind=out.__class__.__name__)
        return out

    # ----- Expose schema-friendly signature for pydantic-ai -----

    # ctx first
    params: list[Parameter] = [
        Parameter("ctx", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=RunContext[TypedStore]),
    ]

    new_annotations: Dict[str, Any] = {"ctx": RunContext[TypedStore]}

    # Copy original parameters, widen annotations to Union[T, StoredModel]
    for p in orig_sig.parameters.values():
        ann = orig_hints.get(p.name, p.annotation)
        if _is_model_from_pool(ann, in_pool):
            widened = Union[ann, StoredModel]  # JSON-schema friendly
            new_ann = widened
        else:
            new_ann = ann

        params.append(
            Parameter(name=p.name, kind=p.kind, default=p.default, annotation=new_ann)
        )
        new_annotations[p.name] = new_ann

    # Return annotation: StoredModel if original says it's in out_pool
    ret_ann = orig_hints.get("return", orig_sig.return_annotation)
    if isinstance(ret_ann, type) and any(issubclass(ret_ann, t) for t in out_pool):
        new_ret = StoredModel
    else:
        new_ret = ret_ann

    new_annotations["return"] = new_ret
    wrapped.__signature__ = Signature(parameters=params, return_annotation=new_ret)
    wrapped.__annotations__ = new_annotations

    return wrapped
# ---------------------------------------------
# 6) Wiring into your Tool registry
# ---------------------------------------------


def make_tool(
    fn: Callable[..., Any],
    name: str,
    description: Optional[str] = None,
    *,
    input_types: Optional[Tuple[type[BaseModel], ...] | list[type[BaseModel]]] = None,
    output_types: Optional[Tuple[type[BaseModel], ...] | list[type[BaseModel]]] = None,
) -> Tool:
    wrapped = wrap_as_stored_tool(fn, input_types=input_types, output_types=output_types)
    return Tool(function=wrapped, name=name, description=description, takes_ctx=True)