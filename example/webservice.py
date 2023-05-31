from operator import add, mul, sub, truediv

from fastapi_soap.request import XMLBody
from fastapi_soap.response import SoapResponse
from fastapi_soap.routes import SoapRouter

from schema import Operands, Result

soap = SoapRouter(name='Calculator', prefix='/Calculator')


@soap.operation(
    name='SumOperation', request_model=Operands, response_model=Result
)
def sum_operation(body: Operands = XMLBody(Operands)):
    result = sum(body.operands)

    return SoapResponse(Result(value=result))
