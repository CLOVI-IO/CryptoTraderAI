class UserBalanceException(Exception):
    """Exception raised for errors in the user balance.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="User balance error occurred"):
        self.message = message
        super().__init__(self.message)
