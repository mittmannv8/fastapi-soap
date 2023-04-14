from pydantic_xml import BaseXmlModel, element

from fastapi_soap.models import BodyContent


class Operator(BaseXmlModel, tag='Operator'):
    value: str


class Operand(BodyContent, tag='Operand'):
    value: float


class Operation(BodyContent, tag='Operation'):
    operands: list[Operand]
    operator: Operator


class OperationResult(BodyContent, tag='OperationResult'):
    result: float = element(tag='Result')


class OperationHistory(BodyContent, tag='Operation'):
    operation: Operation
    result: OperationResult


class ListOperationHistory(BodyContent, tag='OperationHistory'):
    values: list[OperationHistory]


class Operands1(BodyContent, tag='Operands'):
    operands: list[float] = element(tag='Operand')


class Result1(BodyContent, tag='Result'):
    value: float
