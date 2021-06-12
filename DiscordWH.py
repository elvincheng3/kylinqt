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
    def send_qt_delete_embed(self, site, sku):
        try:
            e = discord.Embed(title="Deleting Tasks", description="No Checkouts Detected")
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
    def send_qt_deleteAll_embed(self):
        try:
            e = discord.Embed(title="Deleting All Tasks")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False
    
    def send_qt_receivedHelpQuery(self):
        try:
            e = discord.Embed(title="Help")
            e.add_field(name="Quit KylinQT", value="!quit")
            e.add_field(name="Start QT", value="!start <site> <sku>")
            e.add_field(name="Stop All QT", value="!stop")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False

    def send_qt_receivedStartQuery(self, sku, site):
        try:
            e = discord.Embed(title="Received Query to Start Quicktasks")
            e.add_field(name="SKU", value=sku)
            e.add_field(name="Site", value=site)
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False

    def send_qt_receivedStopQuery(self):
        try:
            e = discord.Embed(title="Received Query to Stop Quicktasks")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False

    def send_qt_receivedQuitQuery(self):
        try:
            e = discord.Embed(title="Received Query to Quit KylinQT")
            e.set_footer(text="KylinQT |  {}".format(datetime.fromtimestamp(time.time())))
            self.webhook.send(embed=e)
            return True
        except Exception as e:
            logging.info(e)
            return False