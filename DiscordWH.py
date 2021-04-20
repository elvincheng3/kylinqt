from discord import Webhook, RequestsWebhookAdapter
import discord
from datetime import datetime
import time
import logging


class DiscordWH:
    # Initialize Discord webhook
    def __init__(self, webhook_id, webhook_token):
        self.webhook = Webhook.partial(webhook_id, webhook_token, adapter=RequestsWebhookAdapter())

    # Send QT Start Embed
    def send_qt_start_embed(self, site, sku):
        try:
            e = discord.Embed(title="Starting Tasks", description="SKU Was Detected!")
            e.add_field(name="SKU", value=sku)
            e.add_field(name="Site", value=site)
            e.set_thumbnail(url="https://images." + site + ".com/pi/" + sku + "/large/" + sku + ".jpeg")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False
    
    # Send QT Stop Embed
    def send_qt_stop_embed(self, site, sku):
        try:
            e = discord.Embed(title="Stopping Tasks", description="No Checkouts Detected")
            e.add_field(name="SKU", value=sku)
            e.add_field(name="Site", value=site)
            e.set_thumbnail(url="https://images." + site + ".com/pi/" + sku + "/large/" + sku + ".jpeg")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False
    
    # Send QT Stop All Embed
    def send_qt_stopAll_embed(self):
        try:
            e = discord.Embed(title="Stopping All Tasks")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False