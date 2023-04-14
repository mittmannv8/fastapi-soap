class FaultException(Exception):
    """Default Fault Exception.

    When raised, the XMLResponse renders this exception as a FaultResponse.
    """

    code: str
    detail: str

    def __init__(self, detail: str, code: str = 'server'):
        """Default Fault Exception.

        Args:
            detail (str): exception details that will rendered as faultstring
            code (str): exception code that will rendered as faultcode

        Example:
        ```
        def some_function(...):
            raise FaultException(
                detail="Ouch! An error here...",
                code="server"
            )
        ```
        ---
        XML Representation
        ```xml
        <Fault>
            <faultcode>server</faultcode>
            <faultstring>Ouch! An error here...</faultstring>
        </Fault>
        ```
        """

        self.detail = detail
        self.code = code


class ClientFaultException(FaultException):
    def __init__(self, detail: str, code: str = 'client'):
        super().__init__(detail, code)
