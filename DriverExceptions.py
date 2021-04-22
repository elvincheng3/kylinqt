class Error(Exception):
    pass

class LoginError(Error):
    def __init__(self):
        self.message = "Failed to Login"

class DriverFailedInitializeError(Error):
    def __init__(self):
        self.message = "Failed to Initialize Driver"