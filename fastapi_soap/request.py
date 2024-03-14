import logging
from typing import Any, Type, TypeVar, cast

from fastapi import Body, Depends
from pydantic import ValidationError

from fastapi_soap.exceptions import ClientFaultException
from fastapi_soap.models import BodyContent, SoapBody, SoapEnvelope, SoapHeader


SoapEnvelopeType = TypeVar('SoapEnvelopeType', bound=SoapEnvelope)
"""Generic type for SoapEnvelope"""


logger = logging.getLogger(__name__)


def XMLBody(model: Type[BodyContent]) -> Any:
    """Dependency to load the body from a soap request.

    Example

    ```
    from fastapi_soap.models import BodyContent

    class PersonSchema(BodyContent, tag="Person"):
        name: str

    def some_webservice(person: PersonSchema = XMLBody(PersonSchema)):
        print(person.name)
    ```
    ---

    Exception handler

    As the BodyContent is a subclass of BaseXmlModel, the schema is validated
    at this stage. The XMLBody function will return a properly XML Client Fault
    """

    def parse_model(data: str = Body()) -> Any:
        model_ = SoapEnvelope[SoapHeader, SoapBody[model]]
        logger.debug(
            "Parsing SOAP envelope using %s model. Request %s", model_, data
        )

        try:
            envelope = cast(
                SoapEnvelope[SoapHeader, SoapBody[model]],
                model_.from_xml(data.encode()),
            )
            return envelope.body.call
        except ValidationError as err:
            raise ClientFaultException(detail=str(err))

    return Depends(parse_model)


def XMLHeader(model: Type[SoapHeader]) -> Any:
    """Dependency to load the header from a soap request.

    Example

    ```
    from fastapi_soap.models import SoapHeader

    class AuthenticatedHeader(BodyContent):
        api_key: str = element(tag="ApiKey")

    def some_webservice(
        header: AuthenticatedHeader = XMLHeader(AuthenticatedHeader)
    ):
        print(header.api_key)
    ```
    ---

    Exception handler

    As the BodyContent is a subclass of BaseXmlModel, the schema is validated
    at this stage. The XMLBody function will return a properly XML Client Fault
    """

    def parse_model(data: str = Body()):
        model_ = SoapEnvelope[model, SoapBody[BodyContent]]
        envelope = cast(
            SoapEnvelope[model, SoapBody[BodyContent]], model_.from_xml(data.encode())
        )
        return envelope.header

    return Depends(parse_model)
