from operator import add, mul, sub, truediv

from fastapi_soap.request import XMLBody
from fastapi_soap.response import SoapResponse
from fastapi_soap.routes import SoapRouter

from .schema import Operands1, Result1

soap = SoapRouter(name='Calculator', prefix='/Calculator')


operators = {'+': add, '-': sub, '*': mul, '/': truediv}

operations_history = []


@soap.operation(
    name='SumOperation', request_model=Operands1, response_model=Result1
)
def sum_operation(body: Operands1 = XMLBody(Operands1)):
    result = sum(body.operands)

    return SoapResponse(Result1(value=result))
