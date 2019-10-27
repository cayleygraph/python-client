import json
from pathlib import Path
from . import snake_case

schema_path = Path(__file__).parent / "schema.json"

def is_step_class(document):
    return (
        document["@type"] == "rdfs:Class"
        and any(
            super_class["@id"] == "linkedql:Step"
            for super_class in document["rdfs:subClassOf"]
        )
    )

def is_restriction(document):
    return document["@type"] == "owl:Restriction"

def is_single_cardinality_restriction(document):
    return document.get("owl:cardinality") is 1

def is_property(document):
    return document["@type"] in {"owl:ObjectProperty", "owl:DatatypeProperty"}

def remove_linked_ql(name):
    return name.replace("linkedql:", "")

def range_to_type(_range):
    if _range["@id"] in {"linkedql:ValueStep", "linkedql:Step"}:
        return "'Path'"
    if _range["@id"] == "xsd:string":
        return "str"
    if _range["@id"] == "xsd:int":
        return "int"
    if _range["@id"] == "xsd:float":
        return "float"
    if _range["@id"] == "xsd:boolean":
        return "bool"
    if _range["@id"] == "linkedql:Operator":
        return "Operator"
    if _range["@id"] == "rdfs:Resource":
        return "Node"
    raise Exception(f"Unexpected range: {_range}")

def normalize_keywords(name):
    if name in {"as", "is", "in", "except"}:
        return "_" + name
    return name

def generate():
    with schema_path.open() as file:
        schema = json.load(file)
        step_classes = []
        restrictions = {}
        properties_by_domain = {}

        for document in schema:
            if is_restriction(document):
                restrictions[document["@id"]] = document
            if is_property(document):
                class_properties = properties_by_domain.setdefault(document["rdfs:domain"]["@id"], [])
                class_properties.append(document)
            if is_step_class(document):
                step_classes.append(document)
        
        print("""from typing import List
    class Node:
        pass

    class Operator:
        pass

    class Path:
        def __init__(self):
            self.cursor = None

        def __add_step(self, step):
            prev_cursor = self.cursor
            self.cursor = step
            if prev_cursor:
                self.cursor = {**self.cursor, "linkedql:from": prev_cursor}""")

        for step_class in step_classes:
            single_properties = set()
            for super_class in step_class["rdfs:subClassOf"]:
                if super_class["@id"] in restrictions:
                    restriction = restrictions[super_class["@id"]]
                    if is_single_cardinality_restriction(restriction):
                        _property = restriction["owl:onProperty"]
                        single_properties.add(_property["@id"])
            method_name = normalize_keywords(snake_case.convert(remove_linked_ql(step_class["@id"])))
            method_str = f"def {method_name}("
            arguments = ["self"]
            mapping = {}
            for _property in properties_by_domain.get(step_class["@id"]):
                argument_name = remove_linked_ql(_property['@id'])
                if argument_name == "from":
                    continue
                mapping[_property["@id"]] = argument_name
                _type = range_to_type(_property["rdfs:range"])
                if _property["@id"] not in single_properties:
                    _type = "List[" + _type + "]"
                arguments.append(f"{argument_name}: {_type}")
            body = ",\n".join(
                '            "' + key + '": ' + value
                for key, value
                in {"@type": '"' + step_class['@id'] + '"', **mapping}.items()
            )
            method_str += ", ".join(arguments) + f""") -> 'Path':
            self.__add_step({{
    {body}
            }})
            return self
            """
            print("    " + method_str)