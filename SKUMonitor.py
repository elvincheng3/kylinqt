import time
from DiscordWH import DiscordWH
from QueueData import QueueData
import logging
from pydispatch import dispatcher

site_list = ["footlocker", "champssports", "footaction", "eastbay", "kidsfootlocker"]
SIGNAL_RESUME = 'RESUME'

class SKUMonitor:
    # Initialize SKUMonitor
    def __init__(self, sku, webhook, driver, queue):
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
        self.queue = queue
    
    # Return SKU
    def getSKU(self):
        return self.sku

    # Check all timestamps and stop tasks if needed
    async def checkTimestamps(self):
        async def check(site):
            if self.sites[site] != 0 and int(time.time() * 1000) - self.sites[site] > 360000:
                logging.info("Stopping tasks with SKU {} on {}".format(self.sku, site))
                self.webhook.send_qt_stop_embed(site=site, sku=self.sku)
                self.sites[site] = 0
                await self.queue.put(QueueData().delete(self.sku, site))
                stopped = True

        stopped = False
        await check("footlocker")
        await check("champssports")
        await check("footaction")
        await check("eastbay")
        await check("kidsfootlocker")

        if stopped:
            dispatcher.send(signal=SIGNAL_RESUME, sender=self)
        return stopped
    
    async def restartIfStopped(self):
        if self.sites["footlocker"] != 0 and int(time.time() * 1000) - self.sites["footlocker"] < 360000:
            logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "footlocker"))
            await self.queue.put(QueueData().create(self.sku, "footlocker"))
        if self.sites["champssports"] != 0 and int(time.time() * 1000) - self.sites["champssports"] < 360000:
            logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "champssports"))
            await self.queue.put(QueueData().create(self.sku, "champssports"))
        if self.sites["footaction"] != 0 and int(time.time() * 1000) - self.sites["footaction"] < 360000:
            logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "footaction"))
            await self.queue.put(QueueData().create(self.sku, "footaction"))
        if self.sites["eastbay"] != 0 and int(time.time() * 1000) - self.sites["eastbay"] < 360000:
            logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "eastbay"))
            await self.queue.put(QueueData().create(self.sku, "eastbay"))
        if self.sites["kidsfootlocker"] != 0 and int(time.time() * 1000) - self.sites["kidsfootlocker"] < 360000:
            logging.info("SKU {} was Stopped by Other SKU, Resuming Tasks on {}".format(self.sku, "kidsfootlocker"))
            await self.queue.put(QueueData().create(self.sku, "kidsfootlocker"))

    async def updateTimestamp(self, timestamp, site):
        if self.sites[site] != 0:
            if self.sites[site] < timestamp:
                self.sites[site] = timestamp 
        else:
            logging.info("SKU {} Found on {}, Starting Tasks".format(self.sku, site))
            self.webhook.send_qt_start_embed(site=site, sku=self.sku)
            await self.queue.put(QueueData().create(self.sku, site))
            self.sites[site] = timestamp