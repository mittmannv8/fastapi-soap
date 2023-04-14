# FastAPI Soap

This package helps to create Soap WebServices using FastAPI (What?!?!)

## Motivation
I know, FastAPI is a REST micro framework, but sometimes is needed expose a Soap Interface on a already running FastAPI application for an legacy client/application that only supports, well, the Soap protocol...

## Installation and dependencies
Only FastAPI, Pydantic and Pydantic XML are required.


## First steps

```python
from fastapi import FastAPI
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
    result = sum(body.operands)
    
    return SoapResponse(
        Result(value=result)
    )


app = FastAPI()
app.include_router(soap)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("example.main:app")
```
_(This script is complete, it should run "as is")_


The WSDL is available on webservice root path for GET method.
```
GET http://localhost:8000/Calculator/
```

