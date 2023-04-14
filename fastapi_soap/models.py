from typing import Generic, Optional, TypeVar

from pydantic_xml import BaseGenericXmlModel, BaseXmlModel, element


class SoapHeader(
    BaseXmlModel,
    tag='Header',
    ns='soap',
):
    """Soap header abstract definition.

    Examples:
    ```
    class MyCustomHeader(SoapHeader):
        api_key: str = element(tag="XApiKey")

    # XML representation
    <soap:Header>
        <XApiKey>my-ultra-secret-api-key</XApiKey>
    </soap:Header>

    # JSON representation
    {
        "header": {
            "api_key": "my-ultra-secret-api-key"
        }
    }
    ```
    """


class BodyContent(BaseXmlModel):
    """Soap body abstract content model.

    Example
    ```
    class SomeResponse(BodyContent):
        some_tag: str = element(tag="SomeTag")
    ```
    """


class EmptyContent(BodyContent):
    """Helper model for empty requests."""


class FaultResponse(BodyContent, tag='Fault'):
    """Soap Fault response model."""

    faultcode: str = element()
    faultstring: str = element()


BodyContentType = TypeVar(
    'BodyContentType', bound=BodyContent | FaultResponse | BaseXmlModel
)
"""Generic type for body content. Accepts a BodyContent or a FaultResponse"""


class SoapBody(
    BaseGenericXmlModel,
    Generic[BodyContentType],
    tag='Body',
    ns='soap',
):
    """Soap body abstract model definition.

    Example:

    ```
    # Body content model. Generally this model is an operation representation.
    class GetPersonOperation(BaseXmlModel, tag="GetPerson"):
        name: str = element(tag="Name")

    # Define the SoapBody with the content model
    BodyModel: SoapBody[GetPersonOperation]
    ```
    ---
    XML representation
    ```xml
    <soap:Body>
        <GetPerson>
            <Name>John</Name>
        </GetPerson>
    </soap:Body>
    ```
    ---
    JSON representation
    ```json
    {
        "body": {
            "call": {
                "name": "John"
            }
        }
    }
    ```
    """

    call: Optional[BodyContentType]


HeaderType = TypeVar('HeaderType', bound=SoapHeader)
"""Generic type for SoapHeader model"""

BodyType = TypeVar('BodyType', bound=SoapBody)
"""Generic type for Body model"""


class SoapEnvelope(
    BaseGenericXmlModel,
    Generic[HeaderType, BodyType],
    tag='Envelope',
    ns='soap',
    nsmap={
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
    },
):
    """Soap Envelope abstract definition.

    Example:

    ```
    RequestEnvelope: SoapEnvelope[MyCustomHeader, SoapBody[GetPersonOperation]]
    ```
    ---
    XML representation
    ```xml
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Header>
            <XApiKey>my-ultra-secret-api-key</XApiKey>
        </soap:Header>
        <soap:Body>
            <GetPerson>
                <Name>John</Name>
            </GetPerson>
        </soap:Body>
    </soap:Envelope>
    ```
    """

    header: Optional[HeaderType]
    body: BodyType
