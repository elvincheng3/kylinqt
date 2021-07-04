import time
from DiscordWH import DiscordWH
from QueueData import QueueData
import logging
from pydispatch import dispatcher

site_list = ["footlocker", "champssports", "footaction", "eastbay", "kidsfootlocker"]
SIGNAL_RESUME = 'RESUME'

class SKUMonitor:
    # Initialize SKUMonitor
    def __init__(self, sku, webhook, driver, queue, pause_interval):
        self.sku = sku
        self.sites = {
            "footlocker": 0,
            "champssports": 0,
            "footaction": 0,
            "eastbay": 0,
            "kidsfootlocker": 0
        }
        self.pause = {
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
        self.pause_interval = pause_interval
    
    # Return SKU
    def getSKU(self):
        return self.sku

    # Check all timestamps and stop tasks if needed
    async def checkTimestamps(self):
        async def check(site):
            if self.sites[site] != 0 and int(time.time() * 1000) - self.sites[site] > 360000:
                logging.info("Deleting tasks with SKU {} on {}".format(self.sku, site))
                self.webhook.send_qt_delete_embed(site=site, sku=self.sku)
                self.sites[site] = 0
                await self.queue.put(QueueData().delete(self.sku, site))

                logging.info("Ignoring SKU {} for {}s".format(self.sku, self.pause_interval))
                self.pause[site] = int(time.time() * 1000)

                return True
            return False

        ftl_check = await check("footlocker")
        champs_check = await check("champssports")
        fa_check = await check("footaction")
        eb_check = await check("eastbay")
        kftl_check = await check("kidsfootlocker")

        if ftl_check or champs_check or fa_check or eb_check or kftl_check:
            await self.restartIfStopped()
            logging.info("Attempted to restart deleted tasks")
            return True
        return False
    
    async def restartIfStopped(self):
        async def resumeLogging(sku, site):
            logging.info("SKU {} was Deleted by Other SKU, Resuming Tasks on {}".format(sku, site))
            await self.queue.put(QueueData().create(sku, site))

        for site in site_list:
            if self.sites[site] != 0 and int(time.time() * 1000) - self.sites[site] < 360000:
                await resumeLogging(self.sku, site)
        
        # if self.sites["footlocker"] != 0 and int(time.time() * 1000) - self.sites["footlocker"] < 360000:
        #     await resumeLogging(self.sku, "footlocker")
        # if self.sites["champssports"] != 0 and int(time.time() * 1000) - self.sites["champssports"] < 360000:
        #     await resumeLogging(self.sku, "champssports")
        # if self.sites["footaction"] != 0 and int(time.time() * 1000) - self.sites["footaction"] < 360000:
        #     await resumeLogging(self.sku, "footaction")
        # if self.sites["eastbay"] != 0 and int(time.time() * 1000) - self.sites["eastbay"] < 360000:
        #     await resumeLogging(self.sku, "eastbay")
        # if self.sites["kidsfootlocker"] != 0 and int(time.time() * 1000) - self.sites["kidsfootlocker"] < 360000:
        #     await resumeLogging(self.sku, "kidsfootlocker")
        

    async def updateTimestamp(self, timestamp, site):
        if self.sites[site] != 0:
            if self.sites[site] < timestamp:
                self.sites[site] = timestamp 
        else:
            if int(time.time() * 1000) - self.pause[site] > (self.pause_interval * 1000): #TODO: #2 Create dedicated function to unpause at regular interval
                logging.info("SKU {} Unpaused".format(self.sku))
                self.pause[site] = 0
            if self.pause[site] == 0: 
                logging.info("SKU {} Found on {}, Starting Tasks".format(self.sku, site))
                await self.queue.put(QueueData().create(self.sku, site))
                self.webhook.send_qt_start_embed(site=site, sku=self.sku)
                self.sites[site] = timestamp
            else:
                logging.info("SKU {} Found While Paused".format(self.sku))