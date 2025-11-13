from control_agent.agent.common import *
from control_agent.agent.ctx import SimContext, FmuContext, StateDeps

from pydantic_ai.tools import ToolDefinition
from typing import Callable, Any
from docstring_parser import parse, Docstring, DocstringParam, DocstringReturns, compose, DocstringStyle

from pydantic_ai._function_schema import function_schema, _takes_ctx, FunctionSchema, _is_call_ctx, doc_descriptions, _build_schema
from pydantic_ai.tools import Tool, GenerateToolJsonSchema, JsonSchemaValue
from pydantic._internal import _decorators, _generate_schema, _typing_extra
from pydantic_core import SchemaValidator, core_schema
from pydantic._internal._config import ConfigWrapper
from pydantic import ConfigDict

from typing import Any, get_origin, get_args, Union

def normalize_type_name(t: Any) -> str:
    """
    Convert Python types (including generics and unions) into readable type names.
    """
    if t is None:
        return "None"

    # Built-in types: int, str, bool, Path, etc.
    if isinstance(t, type):
        return t.__name__

    origin = get_origin(t)
    args = get_args(t)

    # Optional[T] = Union[T, NoneType]
    if origin is Union:
        parts = [normalize_type_name(a) for a in args]
        if type(None) in args and len(args) == 2:
            # Optional[T]
            non_none = [p for p in args if p is not type(None)][0]
            return f"Optional[{normalize_type_name(non_none)}]"
        else:
            # General union
            return f"Union[{', '.join(normalize_type_name(a) for a in args)}]"

    # Python 3.10+ union operator | produces types.UnionType
    if isinstance(t, type(int | None)):
        parts = args
        if type(None) in parts and len(parts) == 2:
            non_none = [p for p in parts if p is not type(None)][0]
            return f"Optional[{normalize_type_name(non_none)}]"
        return f"Union[{', '.join(normalize_type_name(a) for a in parts)}]"

    # Parametrized generics: e.g. StateDeps[SimContext]
    if origin is not None:
        origin_name = origin.__name__ if hasattr(origin, "__name__") else str(origin)
        arg_names = ", ".join(normalize_type_name(a) for a in args)
        return f"{origin_name}[{arg_names}]"

    # Last fallback
    return str(t)

def make_docstring(
    external_fn: Callable[[Any], Any],
    tool_fn: Callable[[Any], Any]) -> JsonSchemaValue:
    import json
    schema_generator = GenerateToolJsonSchema()
    og_scema = function_schema( external_fn, GenerateToolJsonSchema, takes_ctx=_takes_ctx(external_fn))
    print(json.dumps(og_scema.json_schema, indent=4))

    og_props = og_scema.json_schema.get("properties", {})

    tool_schema = function_schema( tool_fn, GenerateToolJsonSchema, takes_ctx=_takes_ctx(tool_fn))    
    tool_props = tool_schema.json_schema.get("properties", {})
    tool_schema.description = og_scema.description
    
    docstring_external = parse(str(external_fn.__doc__))
    docstring_tool = parse(str(tool_fn.__doc__))

    seen_params = set()

    params = docstring_tool.params
    for param in docstring_external.params:
        if isinstance(param, DocstringParam):
            for p in docstring_tool.params:
                if isinstance(p, DocstringParam) and p.arg_name == param.arg_name:
                    p.description = param.description
                    seen_params.add(param.arg_name)
                    break

    if docstring_external.returns and docstring_tool.returns:
        if docstring_external.returns.type_name == docstring_tool.returns.type_name:
            docstring_tool.returns.description = docstring_external.returns.description
    
    docstring_tool.long_description = docstring_external.long_description
    docstring_tool.short_description = docstring_external.short_description
    docstring_tool.blank_after_short_description = True
    docstring_tool.blank_after_long_description = True
    #docstring_tool.meta = docstring_external.meta
    meta = []
    # add missing params from tool schema
    for _name, _type in tool_fn.__annotations__.items():
    
        if _name not in seen_params:
            _desc = tool_props.get("description", "")
            _type = normalize_type_name(tool_fn.__annotations__.get(_name, None))
            _is_optional = False
            for t in tool_props.get(_name, {}).get("anyOf", []):
                if t.get("type", "") == "null": _is_optional = True


            meta.append(
                DocstringParam(args=["param"], description=_desc, arg_name=_name,
                type_name=_type, is_optional=_is_optional, default=tool_props.get(_name, {}).get("default", None)))
            seen_params.add(_name)
    
    docstring_tool.meta = meta
    return compose(docstring_tool, style=DocstringStyle.GOOGLE)


if __name__ == "__main__":
    from control_agent.agent.common import *
    from control_agent.agent.agent import create_agent

    def some_tool(bar: int=42, baz: Optional[str]= None) -> int:
        """
        This is a test tool.
        
        Purpouse:
            To test the tool preparation function.

        Important:
            This tool is important. 

        Args:
            bar: the meaning of life
            baz: what comes after..

        Returns:
            int: The sum of the two arguments


        Purpouse:
            To test the tool preparation function.

        Important:
            This tool is important.        
        
        """
        return bar + len(baz)

    def my_custom_tool(ctx: StateDeps[SimContext], bar: int, baz: str) -> bool:
        """
        Params:
            ctx: the context
        """
        return some_tool(bar, baz) == 42
    
    docstring = make_docstring(some_tool, my_custom_tool)
    print("--------------------------------")
    print(docstring)

    print("--------------------------------")
    print(some_tool.__doc__)

    print(my_custom_tool.__annotations__)

    t = Tool(my_custom_tool, name="my_custom_tool", description=make_docstring(some_tool, my_custom_tool))
    print(t.description)