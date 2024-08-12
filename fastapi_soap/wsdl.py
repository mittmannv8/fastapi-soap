from typing import Optional, Any
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from fastapi import Request
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_xml import BaseXmlModel
from pydantic_xml.model import XmlEntityInfo, XmlModelMeta

nsmap = {"xmlns:xs": "http://www.w3.org/2001/XMLSchema"}

PYTHON_XSD_TYPE_MAP = {
    "str": "string",
    "int": "integer",
    "float": "double",
    "bool": "boolean",
    "date": "date",
    "time": "time",
    "datetime": "dateTime",
    "AnyUrl": "anyURI",
    "PositiveInt": "positiveInteger",
}
nsmap = {
    "xmlns:soap": "http://schemas.xmlsoap.org/wsdl/soap/",
    "xmlns:wsdl": "http://schemas.xmlsoap.org/wsdl/",
    "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
    "xmlns:wsdlsoap": "http://schemas.xmlsoap.org/wsdl/soap/",
}


def generate_xsd_element(
    model: Optional[BaseXmlModel] = None,
    field_info: Optional[FieldInfo] = None,
) -> Element:
    xsd_element = Element("xs:element")
    model_ = model or (field_info.annotation if field_info else None)

    if model is not None:
        xsd_element.set("name", getattr(model, "__xml_tag__", model.__name__))
    elif field_info:
        if isinstance(field_info, XmlEntityInfo):
            tag_name = field_info.path or field_info.alias
        else:
            tag_name = getattr(field_info, "alias", None) or getattr(
                field_info, "name", "Unknown"
            )
        xsd_element.set("name", tag_name)
    elif hasattr(model_, "__xml_tag__"):
        xsd_element.set("name", model_.__xml_tag__)
    else:
        xsd_element.set("name", "Unknown")

    if isinstance(model_, XmlModelMeta):
        complex_type = Element("xs:complexType")
        sequence = ET.SubElement(complex_type, "xs:sequence")

        for field_name, field in model_.model_fields.items():
            tag = generate_xsd_element(field_info=field)
            sequence.append(tag)

        xsd_element.append(complex_type)
    else:
        element_type = PYTHON_XSD_TYPE_MAP.get(
            str(model_.__name__ if model_ else "str"), "string"
        )
        xsd_element.set("type", f"xs:{element_type}")

    if field_info:
        if isinstance(field_info.annotation, list):
            xsd_element.set("minOccurs", str(0))
            xsd_element.set("maxOccurs", "unbounded")
        elif field_info.default is not PydanticUndefined:
            xsd_element.set("minOccurs", "0")

    return xsd_element


def generate_xsd_schema_etree(models: list[BaseXmlModel]) -> Element:
    schema = Element("xs:schema", nsmap)

    for model in models:
        if tag := generate_xsd_element(model=model):
            schema.append(tag)

    return schema


def dump_etree(etree: Element) -> str:
    return tostring(etree).decode()


def generate_wsdl(
    name: str,
    methods: dict[str, dict[str, Any]],
    url: str,
    request: Request,
    documentation: str = "",
) -> Element:
    wsdl = Element("wsdl:definitions", nsmap, name=name)
    SubElement(wsdl, "wsdl:documentation").text = documentation
    types_element = SubElement(wsdl, "wsdl:types")
    port_type_element = SubElement(wsdl, "wsdl:portType", name=name)

    # service
    service_element = SubElement(wsdl, "wsdl:service", name=name)

    types: set[BaseXmlModel] = set()

    for method, models in methods.items():
        method_name = f"{name}{method}"
        operation_element = SubElement(
            port_type_element, "wsdl:operation", name=method_name
        )

        # binding
        binding_element = SubElement(wsdl, "wsdl:binding", name=method_name, type=name)
        SubElement(
            binding_element,
            "soap:binding",
            style="document",
            transport="http://schemas.xmlsoap.org/soap/http",
        )
        binding_operation = SubElement(
            binding_element, "wsdl:operation", name=method_name
        )
        SubElement(binding_operation, "soap:operation", soapAction=method)

        # service
        port_element = SubElement(
            service_element, "wsdl:port", name=method_name, binding=method_name
        )
        SubElement(
            port_element,
            "soap:address",
            location=f'{str(request.url.replace(query="", fragment="")).rstrip("/")}/{method}',
        )

        for action, model in models.items():
            if model is None:
                continue
            types.add(model)

            # message
            message_name = f"{method}{action.title()}"
            message = SubElement(wsdl, "wsdl:message", name=message_name)

            element_type = model.model_config.get("tag", model.__name__)

            SubElement(
                message,
                "wsdl:part",
                name="parameters",
                element=element_type,
            )

            # portType
            wsdl_action = "input" if action == "request" else "output"
            SubElement(operation_element, f"wsdl:{wsdl_action}", message=message_name)

            # binding
            binding_operation_action = SubElement(
                binding_operation, f"wsdl:{wsdl_action}", message=message_name
            )
            SubElement(binding_operation_action, "soap:body", use="literal")

    types_element.append(generate_xsd_schema_etree(list(types)))

    return wsdl
