class QueueData():
    def __init__(self):
        return
    def login(self, user, ps):
        return {
            "type": "LOGIN",
            "data": {
                "user": user,
                "pass": ps
            }
        }
    def create(self, sku, site):
        return {
            "type": "CREATE",
            "data": {
                "sku": sku,
                "site": site
            }
        }
    def delete(self, sku, site):
        return {
            "type": "DELETE",
            "data": {
                "sku": sku,
                "site": site
            }
        }
    def stop(self):
        return {
            "type": "STOP",
            "data": {}
        }