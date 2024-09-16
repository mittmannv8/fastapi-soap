from typing import Optional
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import Request
from pydantic.v1.typing import display_as_type
from pydantic_xml import BaseXmlModel
from pydantic_xml.model import XmlEntityInfo, XmlModelMeta


PYTHON_XSD_TYPE_MAP = {
    'str': 'string',
    'int': 'integer',
    'float': 'double',
    'bool': 'boolean',
    'date': 'date',
    'time': 'time',
    'datetime': 'dateTime',
    'AnyUrl': 'anyURI',
    'PositiveInt': 'positiveInteger',
}
nsmap = {
    'xmlns:soap': 'http://schemas.xmlsoap.org/wsdl/soap/',
    'xmlns:wsdl': 'http://schemas.xmlsoap.org/wsdl/',
    'xmlns:xs': 'http://www.w3.org/2001/XMLSchema',
    'xmlns:wsdlsoap': 'http://schemas.xmlsoap.org/wsdl/soap/',
}


def generate_xsd_element(
    model: Optional[BaseXmlModel] = None,
    model_field: Optional[XmlEntityInfo] = None,
    model_field_name: str = None
) -> Element:
    element = Element('xs:element')
    model_ = model or getattr(model_field, 'annotation')

    if model is not None:
        element.set('name', model.__xml_tag__)
    elif model_field and hasattr(model_field, 'path'):
        tag_name = (
            model_field.path
            or model_field.alias
            or model_field_name
        )
        element.set('name', tag_name)
    elif hasattr(model_, '__xml_tag__'):
        element.set('name', model_.__xml_tag__)
    else:
        element.set('name', model_field_name)

    if isinstance(model_, XmlModelMeta):
        complex_type = Element('xs:complexType')
        sequence = ET.SubElement(complex_type, 'xs:sequence')

        for model_field_name, model_field_ in model_.__fields__.items():
            tag = generate_xsd_element(model_field=model_field_, model_field_name=model_field_name)
            sequence.append(tag)

        element.append(complex_type)

    else:
        element_type = PYTHON_XSD_TYPE_MAP.get(
            display_as_type(model_), 'string'
        )
        element.set('type', f'xs:{element_type}')

    # if model_field and model_field.is_complex():
    #     if model_field.shape == 2:
    #         # TODO: get gt and lt
    #         element.set(
    #             'minOccurs', str(model_field.field_info.min_items or 0)
    #         )
    #         element.set(
    #             'maxOccurs',
    #             str(model_field.field_info.max_items or 'unbounded'),
    #         )
    #     else:
    #         ...

    return element


def generate_xsd_schema_etree(models: list[BaseXmlModel]) -> Element:
    schema = Element('xs:schema', nsmap)

    for model in models:
        if tag := generate_xsd_element(model=model):
            schema.append(tag)

    return schema


def dump_etree(element: Element) -> str:
    return tostring(element).decode()


def generate_wsdl(
    name: str, methods, url: str, request: Request, documentation: str = ''
) -> Element:
    wsdl = Element('wsdl:definitions', nsmap, name=name)
    SubElement(wsdl, 'wsdl:documentation').text = documentation
    types_element = SubElement(wsdl, 'wsdl:types')
    port_type_element = SubElement(wsdl, 'wsdl:portType', name=name)

    # service
    service_element = SubElement(wsdl, 'wsdl:service', name=name)

    types: set[BaseXmlModel] = set()

    for method, models in methods.items():
        method_name = f'{name}{method}'
        operation_element = SubElement(
            port_type_element, 'wsdl:operation', name=method_name
        )

        # binding
        binding_element = SubElement(
            wsdl, 'wsdl:binding', name=method_name, type=name
        )
        SubElement(
            binding_element,
            'soap:binding',
            style='document',
            transport='http://schemas.xmlsoap.org/soap/http',
        )
        binding_operation = SubElement(
            binding_element, 'wsdl:operation', name=method_name
        )
        SubElement(binding_operation, 'soap:operation', soapAction=method)

        # service
        port_element = SubElement(
            service_element, 'wsdl:port', name=method_name, binding=method_name
        )
        SubElement(
            port_element,
            'soap:address',
            location=f'{str(request.url.replace(query="", fragment="")).rstrip("/")}/{method}',
        )

        for action, model in models.items():
            if model is None:
                continue
            types.add(model)

            # message
            message_name = f'{method}{action.title()}'
            message = SubElement(wsdl, 'wsdl:message', name=message_name)

            element_type = getattr(
                model, '__xml_tag__', display_as_type(model)
            )

            SubElement(
                message,
                'wsdl:part',
                name='parameters',
                element=element_type,
            )

            # portType
            wsdl_action = 'input' if action == 'request' else 'output'
            SubElement(
                operation_element, f'wsdl:{wsdl_action}', message=message_name
            )

            # binding
            binding_operation_action = SubElement(
                binding_operation, f'wsdl:{wsdl_action}', message=message_name
            )
            SubElement(binding_operation_action, 'soap:body', use='literal')

    types_element.append(generate_xsd_schema_etree(list(types)))

    return wsdl
