class Session:
    # Create new session tracker for Discord Gateway
    def __init__(self):
        self.s = "null"
        self.session_id = ""
        self.retry = False
        
    # Set a new S value
    def setS(self, s):
        self.s = s

    # Set a new SessionID
    def setSessionId(self, session_id):
        self.session_id = session_id

    # Return S value
    def getS(self):
        return self.s

    # Return SessionID value
    def getSessionId(self):
        return self.session_id