from typing import Any

from fastapi import Response
from pydantic_xml import BaseXmlModel

from fastapi_soap.models import SoapBody, SoapEnvelope, SoapHeader


class SoapResponse(Response):
    """FastAPI Response that renders a Soap XML response."""

    media_type = 'text/xml'

    def __init__(
        self,
        *args,
        soap_header: SoapHeader = SoapHeader(),
        envelope_wrap: bool = True,
        **kwargs,
    ) -> None:
        """
        Args:
            soap_header (SoapHeader, optional): _description_. Defaults to SoapHeader().
            envelope_wrap (bool, optional): _description_. Defaults to True.
            args (tuple[Any, ...]): Any positional argument for Response
            kwargs (dict[str, Any]): Any keyword argument for Response

        Example:

        ```
        class MyResponse(BodyContent, tag="Response"):
            result: int = element(tag="Result")

        @soap.operation(..., response_model=MyResponse)
        def some_operation_function(...):
            return SoapResponse(MyResponse(result=42))
        ```
        ---
        XML Response
        ```xml
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header/>
            <soap:Response>
                <Result>42</Result>
            </soap:Response>
        </soap:Envelope>
        ```
        """

        self._soap_header = soap_header
        self._envelope_wrap = envelope_wrap
        super().__init__(*args, **kwargs)

    def render(self, content: Any) -> str | bytes:
        if isinstance(content, BaseXmlModel):
            if not self._envelope_wrap:
                return content.to_xml(encoding='UTF-8')

            soap_body_model = SoapBody[content.__class__]
            envelope_model = SoapEnvelope[
                self._soap_header.__class__, soap_body_model
            ]
            envelope: envelope_model = envelope_model(
                header=self._soap_header, body=soap_body_model(call=content)
            )
            return envelope.to_xml(encoding='UTF-8')

        return content if not isinstance(content, str) else content.encode()
