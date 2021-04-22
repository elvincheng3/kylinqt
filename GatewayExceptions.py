class Error(Exception):
    pass

class HeartFailedError(Error):
    def __init__(self):
        self.message = "Heart Failed"