from pydantic_xml import element

from fastapi_soap.models import BodyContent


class Operands(BodyContent, tag='Operands'):
    operands: list[float] = element(tag='Operand')


class Result(BodyContent, tag='Result'):
    value: float
