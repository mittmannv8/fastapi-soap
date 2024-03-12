from typing import Callable, Optional, Type

from fastapi import Request, Response
from fastapi.routing import APIRoute, APIRouter
from fastapi.types import DecoratedCallable
from pydantic_xml import BaseXmlModel

from fastapi_soap.exceptions import FaultException
from fastapi_soap.models import FaultResponse
from fastapi_soap.response import SoapResponse
from fastapi_soap.wsdl import dump_etree, generate_wsdl


class SoapRoute(APIRoute):
    """FastAPI API Route extended class.

    This APIRoute aims to handle any exception of an Soap WebService as a
    Soap Fault response instead of manually add a new exception handler
    to FastAPI app.
    """

    async def exception_response(
        self, fault, status_code: int = 500
    ) -> Response:
        return SoapResponse(fault, status_code=status_code)

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)

            except FaultException as fault:
                return await self.exception_response(
                    FaultResponse(
                        faultcode=fault.code, faultstring=fault.detail
                    )
                )
            except Exception as exc:
                return await self.exception_response(
                    FaultResponse(
                        faultcode='server',
                        faultstring=f'Internal Error: {exc}',
                    )
                )

        return custom_route_handler


class SoapRouter(APIRouter):
    """Custom Router to create Soap WebServices."""

    def __init__(self, *args, name: str, **kwargs) -> None:
        """
        Attrs:
            name (str): WebService Name
            prefix (str): FastAPI base path for the webservice
            kwargs (dict): All FastAPI APIRouter parameters

        Example:
        ```
        soap = SoapRouter(name="CalculatorWebService", prefix="/Calculator")
        ```
        ---

        WSDL

        The soap router provides a WSDL file for all registered operations on:

        GET http(s)://hostname/Calculator
        """
        super().__init__(
            *args,
            default_response_class=SoapResponse,
            route_class=SoapRoute,
            **kwargs,
        )

        self._requests = set()
        self._responses = set()

        self._name = name

        self._methods = {}
        self.add_api_route(
            '/', self._generate_wsdl, methods=['GET'], status_code=200
        )

    def _generate_wsdl(self, request: Request):
        wsdl = generate_wsdl(self._name, self._methods, url=self.prefix, request=request)
        return SoapResponse(dump_etree(wsdl), envelope_wrap=False)

    def operation(
        self,
        *,
        name: str,
        request_model: Optional[Type[BaseXmlModel]] = None,
        response_model: Optional[Type[BaseXmlModel]] = None,
        status_code: int = 200,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Register the soap operation (also known as method) to the webservice.

        Attrs:
            name (str): Represents an Soap Interface
            request_model (BodyContent): Expected Soap input Message definition
            response_model (BodyContent): Expected Soap output Message definition

        ---

        Example:
        ```
        soap = SoapRouter(name="CalculatorWebService", prefix="/Calculator")

        @soap.operation(name="Sum", request_model: ..., response_model: ...)
        def sum(...):
            ...
        ```
        """

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self._methods.update(
                {name: {'request': request_model, 'response': response_model}}
            )
            self.add_api_route(
                f'/{name}',
                func,
                methods=['POST'],
                response_class=SoapResponse,
                status_code=status_code,
            )
            return func

        return decorator
