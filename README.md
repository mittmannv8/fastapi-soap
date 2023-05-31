# FastAPI Soap

This package helps to create Soap WebServices using FastAPI (What?!?!)

## Motivation
I know, FastAPI is a REST micro framework, but sometimes is needed to expose a Soap Interface on a already running FastAPI application for an legacy client/application that only supports, well, the Soap protocol...

## Installation and dependencies
Only FastAPI, Pydantic and Pydantic XML are required.


## First steps

```python
from fastapi import FastAPI
from pydantic_xml import element
from fastapi_soap import SoapRouter, XMLBody, SoapResponse
from fastapi_soap.models import BodyContent


class Operands(BodyContent, tag="Operands"):
    operands: list[float] = element(tag="Operand")

class Result(BodyContent, tag="Result"):
    value: float

soap = SoapRouter(name='Calculator', prefix='/Calculator')

@soap.operation(
    name="SumOperation",
    request_model=Operands,
    response_model=Result
)
def sum_operation(body: Operands = XMLBody(Operands)):
    """
    Receives an Operands object and returns a Result object.

    Args:
        body (Operands): Operands object with a list of operands
    """
    result = sum(body.operands)
    
    return SoapResponse(
        Result(value=result)
    )


app = FastAPI()

app.include_router(soap)

if __name__ == '__main__':
    import uvicorn  # Any Python ASGI web server can be used
    uvicorn.run("example.main:app")
```
_(This script is complete, it should run "as is")_


The WSDL is available on webservice root path for GET method.
```
GET http://localhost:8000/Calculator?wsdl
```


## Examples
XML Request

```xml
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
        <Operands>
            <!--Zero or more repetitions:-->
            <Operand>1</Operand>
            <Operand>2</Operand>
            <Operand>3</Operand>
        </Operands>
</soapenv:Envelope>
```

For this example, the sum_operation function will receive an Pydantic object as body

```python
print(body)
# Output Operands(operands=[1.0, 2.0, 3.0])

print(body.operands)
# Output [1.0, 2.0, 3.0]

```
