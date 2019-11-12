import ast
import astor
import json
from pathlib import Path
from typing import Dict, List
from . import snake_case

directory = Path(__file__).parent
schema_path = directory / "schema.json"
header_path = directory / "header.py"


def is_step_class(document):
    return document["@type"] == "rdfs:Class" and any(
        super_class["@id"] == "linkedql:Step"
        for super_class in document["rdfs:subClassOf"]
    )


def is_restriction(document):
    return document["@type"] == "owl:Restriction"


def is_single_cardinality_restriction(document):
    return document.get("owl:cardinality") is 1


def is_property(document):
    return document["@type"] in {"owl:ObjectProperty", "owl:DatatypeProperty"}


def remove_linked_ql(name):
    return name.replace("linkedql:", "")


def range_to_type(_range) -> ast.expr:
    if _range["@id"] in {"linkedql:ValueStep", "linkedql:Step"}:
        return ast.Str(s="Path")
    if _range["@id"] == "xsd:string":
        return ast.Name(id="str")
    if _range["@id"] == "xsd:int":
        return ast.Name(id="int")
    if _range["@id"] == "xsd:float":
        return ast.Name(id="float")
    if _range["@id"] == "xsd:boolean":
        return ast.Name(id="bool")
    if _range["@id"] == "linkedql:Operator":
        return ast.Name(id="Operator")
    if _range["@id"] == "rdfs:Resource":
        return ast.Attribute(
            value=ast.Attribute(value=ast.Name(id="rdflib"), attr="term"), attr="Node"
        )
    raise Exception(f"Unexpected range: {_range}")


def normalize_keywords(name):
    if name in {"as", "is", "in", "except"}:
        return name + "_"
    return name


def generate() -> str:
    module = astor.code_to_ast.parse_file(header_path)
    # print(astor.dump_tree(tree))
    with schema_path.open() as file:
        schema = json.load(file)

    class_def = module.body[-1]
    assert isinstance(class_def, ast.ClassDef) and class_def.name == "Path"

    step_classes: List[dict] = []
    restrictions: Dict[str, dict] = {}
    properties_by_domain: Dict[str, List[dict]] = {}

    for document in schema:
        if is_restriction(document):
            restrictions[document["@id"]] = document
        if is_property(document):
            class_properties = properties_by_domain.setdefault(
                document["rdfs:domain"]["@id"], []
            )
            class_properties.append(document)
        if is_step_class(document):
            step_classes.append(document)

    for step_class in step_classes:
        single_properties = set()
        for super_class in step_class["rdfs:subClassOf"]:
            if super_class["@id"] in restrictions:
                restriction = restrictions[super_class["@id"]]
                if is_single_cardinality_restriction(restriction):
                    _property = restriction["owl:onProperty"]
                    single_properties.add(_property["@id"])
        method_name = normalize_keywords(
            snake_case.convert(remove_linked_ql(step_class["@id"]))
        )
        args = ast.arguments(
            args=[ast.arg(arg="self", annotation=None)],
            vararg=None,
            kwonlyargs=None,
            kw_defaults=None,
            kwarg=None,
            defaults=[],
        )
        name_to_property_name: Dict[str, ast.Str] = {}
        for _property in properties_by_domain[step_class["@id"]]:
            argument_name = remove_linked_ql(_property["@id"])
            if argument_name == "from":
                continue
            name_to_property_name[argument_name] = ast.Str(_property["@id"])
            _type = range_to_type(_property["rdfs:range"])
            if _property["@id"] not in single_properties:
                _type = ast.Subscript(
                    value=ast.Attribute(value=ast.Name(id="typing"), attr="List"),
                    slice=ast.Index(value=_type),
                )
            args.args.append(ast.arg(arg=argument_name, annotation=_type))
        keys = [name_to_property_name[arg.arg] for arg in args.args[1:]]
        values = [ast.Name(arg.arg) for arg in args.args[1:]]
        step_dict = ast.Dict(
            keys=[ast.Str("@type"), *keys], values=[ast.Str(step_class["@id"]), *values]
        )
        function_def = ast.FunctionDef(
            name=method_name,
            args=args,
            returns=ast.Str(s="Path"),
            decorator_list=[],
            body=[
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="self"), attr="__add_step"
                        ),
                        args=[step_dict],
                        keywords=[],
                    )
                ),
                ast.Return(value=ast.Name(id="self")),
            ],
        )
        class_def.body.append(function_def)
    return astor.to_source(module)
