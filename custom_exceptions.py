class UserBalanceException(Exception):
    """Exception raised for errors in the user balance.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="User balance error occurred"):
        self.message = message
        super().__init__(self.message)


class OrderException(Exception):
    """Exception raised for errors in the order creation.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Order creation error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Exception raised for authentication errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Authentication error occurred"):
        self.message = message
        super().__init__(self.message)
