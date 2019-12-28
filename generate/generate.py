import ast
import astor
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Dict, List, Iterator, Set
from . import snake_case

directory = Path(__file__).parent
schema_path = directory / "schema.json"
header_path = directory / "header.py"


def normalize_list(obj) -> list:
    if isinstance(obj, list):
        return obj
    return [obj]


CLASS_TYPES: Set[str] = {"rdfs:Class", "owl:Class"}
STEP_CLASSES_IDS: Set[str] = {"linkedql:PathStep", "linkedql:IteratorStep"}


def is_step_class(document: dict) -> bool:
    super_classes = normalize_list(document.get("rdfs:subClassOf", []))
    super_classes_ids = {super_class["@id"] for super_class in super_classes}
    return document["@type"] in CLASS_TYPES and bool(
        STEP_CLASSES_IDS & super_classes_ids
    )


def is_restriction(document: dict) -> bool:
    return document.get("@type") == "owl:Restriction"


def is_single_cardinality_restriction(document: dict) -> bool:
    return document.get("owl:cardinality") == 1


def is_property(document: dict) -> bool:
    return document["@type"] in {"owl:ObjectProperty", "owl:DatatypeProperty"}


def remove_linked_ql(name):
    return name.replace("linkedql:", "")


def range_to_type(_range: dict) -> ast.expr:
    _id = _range["@id"]
    if _id == "linkedql:PathStep":
        return ast.Constant("Path")
    if _id == "linkedql:PropertyPath":
        return ast.Subscript(
            value=ast.Attribute(value=ast.Name(id="typing"), attr="Union"),
            slice=ast.Index(
                value=ast.ExtSlice(
                    [
                        ast.Name(id="str"),
                        ast.Subscript(
                            value=ast.Attribute(
                                value=ast.Name(id="typing"), attr="List"
                            ),
                            slice=ast.Index(ast.Name("str")),
                        ),
                    ]
                )
            ),
        )
    if _id == "rdf:JSON":
        return ast.Subscript(
            value=ast.Attribute(value=ast.Name(id="typing"), attr="Dict"),
            slice=ast.Index(
                value=ast.ExtSlice([ast.Name(id="str"), ast.Name(id="str")])
            ),
        )
    if _id == "xsd:string":
        return ast.Name(id="str")
    if _id == "xsd:int":
        return ast.Name(id="int")
    if _id == "xsd:float":
        return ast.Name(id="float")
    if _id == "xsd:boolean":
        return ast.Name(id="bool")
    if _id == "linkedql:Operator":
        return ast.Name(id="Operator")
    if _id == "rdfs:Resource":
        return ast.Attribute(
            value=ast.Attribute(value=ast.Name(id="rdflib"), attr="term"), attr="Node"
        )
    if _id == "owl:Thing":
        return ast.Attribute(
            value=ast.Attribute(value=ast.Name(id="rdflib"), attr="term"),
            attr="Identifier",
        )
    raise Exception(f"Unexpected range: {_range}")


def normalize_keywords(name: str) -> str:
    if name in {"as", "is", "in", "except"}:
        return name + "_"
    return name


def get_domains(_property: dict) -> Iterator[dict]:
    domain = _property["rdfs:domain"]
    if "owl:unionOf" in domain:
        for unionMember in domain["owl:unionOf"]["@list"]:
            yield unionMember
    else:
        yield domain


def generate() -> str:
    module = astor.code_to_ast.parse_file(header_path)
    # print(astor.dump_tree(tree))
    with schema_path.open() as file:
        schema = json.load(file)

    class_def = module.body[-1]
    assert isinstance(class_def, ast.ClassDef) and class_def.name == "Path"

    step_classes: List[dict] = []
    properties_by_domain: Dict[str, List[dict]] = {}

    for document in schema["@graph"]:
        if is_property(document):
            for domain in get_domains(document):
                domain = domain["@id"]
                class_properties = properties_by_domain.setdefault(domain, [])
                class_properties.append(document)
        if is_step_class(document):
            step_classes.append(document)

    for step_class in step_classes:
        single_properties: Set[str] = set()
        is_path_step: bool = False
        for super_class in normalize_list(step_class["rdfs:subClassOf"]):
            if super_class["@id"] == "linkedql:PathStep":
                is_path_step = True
            if is_restriction(super_class) and is_single_cardinality_restriction(
                super_class
            ):
                _property = super_class["owl:onProperty"]
                single_properties.add(_property["@id"])
        method_name = normalize_keywords(
            snake_case.convert(remove_linked_ql(step_class["@id"]))
        )
        name_to_property_name: Dict[str, ast.Constant] = {}
        properties = properties_by_domain.get(step_class["@id"], [])
        positional_args = [ast.arg(arg="self", annotation=None)]
        kwonlyargs = []
        for _property in sorted(properties, key=lambda _property: _property["@id"]):
            argument_name = remove_linked_ql(_property["@id"])
            if argument_name == "from":
                continue
            name_to_property_name[argument_name] = ast.Constant(_property["@id"])
            _type = range_to_type(_property["rdfs:range"])
            if _property["@id"] not in single_properties:
                _type = ast.Subscript(
                    value=ast.Attribute(value=ast.Name(id="typing"), attr="List"),
                    slice=ast.Index(value=_type),
                )
            arg = ast.arg(arg=argument_name, annotation=_type)
            if len(properties) <= 2:
                positional_args.append(arg)
            else:
                kwonlyargs.append(arg)
        args = ast.arguments(
            args=positional_args,
            vararg=None,
            kwonlyargs=kwonlyargs or None,
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        )
        values = [ast.Name(name) for name in name_to_property_name.keys()]
        keys = [name_to_property_name[value.id] for value in values]
        step_dict = ast.Dict(
            keys=[ast.Constant("@type"), *keys],
            values=[ast.Constant(step_class["@id"]), *values],
        )
        returns = ast.Constant("Path") if is_path_step else ast.Name(id="FinalPath")
        method = "__add_step" if is_path_step else "__add_final_step"
        comment = step_class["rdfs:comment"]
        docstring_indent = " " * 8
        docstring = ast.Expr(
            ast.Constant(f"\n{docstring_indent + comment}\n{docstring_indent}")
        )
        function_def = ast.FunctionDef(
            name=method_name,
            args=args,
            returns=returns,
            decorator_list=[],
            body=[
                docstring,
                ast.Return(
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id="self"), attr=method),
                        args=[step_dict],
                        keywords=[],
                    )
                ),
            ],
        )
        class_def.body.append(function_def)
    return astor.to_source(module)
