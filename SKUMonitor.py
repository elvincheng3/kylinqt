import time
from DiscordWH import DiscordWH
import logging

class SKUMonitor:
    # Initialize SKUMonitor
    def __init__(self, sku, webhook, driver):
        self.sku = sku
        self.sites = {
            "footlocker": 0,
            "champssports": 0,
            "footaction": 0,
            "eastbay": 0,
            "kidsfootlocker": 0
        }
        self.status = False
        self.webhook = webhook
        self.driver = driver
    
    # Return SKU
    def getSKU(self):
        return self.sku

    # Check all timestamps and stop tasks if needed
    def checkTimestamps(self):
        stopped = False
        if self.sites["footlocker"] != 0 and int(time.time() * 1000) - self.sites["footlocker"] > 360000:
            logging.info("Stopping tasks with SKU {} on {}".format(self.sku, "footlocker"))
            # TODO: Error handling for qt
            self.webhook.send_qt_stop_embed(site="footlocker", sku=self.sku)
            self.sites["footlocker"] = 0
            successfully_stopped = False
            while not successfully_stopped:
                successfully_stopped = self.driver.delete_all_tasks()
            stopped = True
        if self.sites["champssports"] != 0 and int(time.time() * 1000) - self.sites["champssports"] > 360000:
            logging.info("Stopping tasks with SKU {} on {}".format(self.sku, "champssports"))
            # TODO: Error handling for qt
            self.webhook.send_qt_stop_embed(site="champssports", sku=self.sku)
            self.sites["champssports"] = 0
            successfully_stopped = False
            while not successfully_stopped:
                successfully_stopped = self.driver.delete_all_tasks()
            stopped = True
        if self.sites["footaction"] != 0 and int(time.time() * 1000) - self.sites["footaction"] > 360000:
            logging.info("Stopping tasks with SKU {} on {}".format(self.sku, "footaction"))
            # TODO: Error handling for qt
            self.webhook.send_qt_stop_embed(site="footaction", sku=self.sku)
            self.sites["footaction"] = 0
            successfully_stopped = False
            while not successfully_stopped:
                successfully_stopped = self.driver.delete_all_tasks()
            stopped = True
        if self.sites["eastbay"] != 0 and int(time.time() * 1000) - self.sites["eastbay"] > 360000:
            logging.info("Stopping tasks with SKU {} on {}".format(self.sku, "eastbay"))
            # TODO: Error handling for qt
            self.webhook.send_qt_stop_embed(site="eastbay", sku=self.sku)
            self.sites["eastbay"] = 0
            successfully_stopped = False
            while not successfully_stopped:
                successfully_stopped = self.driver.delete_all_tasks()
            stopped = True
        if self.sites["kidsfootlocker"] != 0 and int(time.time() * 1000) - self.sites["kidsfootlocker"] > 360000:
            logging.info("Stopping tasks with SKU {} on {}".format(self.sku, "kidsfootlocker"))
            # TODO: Error handling for qt
            self.webhook.send_qt_stop_embed(site="kidsfootlocker", sku=self.sku)
            self.sites["kidsfootlocker"] = 0
            successfully_stopped = False
            while not successfully_stopped:
                successfully_stopped = self.driver.delete_all_tasks()
            stopped = True
        return stopped
    
    def restartIfStopped(self):
        if self.status == False:
            if self.sites["footlocker"] != 0 and int(time.time() * 1000) - self.sites["footlocker"] < 360000:
                logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "footlocker"))
                self.status = True
            if self.sites["champssports"] != 0 and int(time.time() * 1000) - self.sites["champssports"] < 360000:
                logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "champssports"))
                self.status = True
            if self.sites["footaction"] != 0 and int(time.time() * 1000) - self.sites["footaction"] < 360000:
                logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "footaction"))
                self.status = True
            if self.sites["eastbay"] != 0 and int(time.time() * 1000) - self.sites["eastbay"] < 360000:
                logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "eastbay"))
                self.status = True
            if self.sites["kidsfootlocker"] != 0 and int(time.time() * 1000) - self.sites["kidsfootlocker"] < 360000:
                logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "kidsfootlocker"))
                self.status = True

    def resetStatus(self):
        self.status = False

    def updateTimestamp(self, timestamp, site):
        if self.sites[site] != 0:
            if self.sites[site] < timestamp:
                self.sites[site] = timestamp 
        else:
            logging.info("SKU {} Found on {}, Starting Tasks".format(self.sku, site))
            # TODO: Error handling for qt
            self.webhook.send_qt_start_embed(site=site, sku=self.sku)
            successfully_started = False
            while not successfully_started:
                successfully_started = self.driver.create_task(self.sku, site)
            self.sites[site] = timestamp
            self.status = True