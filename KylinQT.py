import time
import json
from datetime import datetime
import logging
import csv
import random
import websockets
import asyncio
from os import path
from aioconsole import ainput

from DashboardDriver import DashboardDriver
from Session import Session
from DiscordWH import DiscordWH
from SKUMonitor import SKUMonitor

logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, handlers=[
    logging.FileHandler("task.log"),
    logging.StreamHandler()
])

def runGateway():

    async def heartbeat(ws, interval):
        """Send every interval ms the heatbeat message."""
        try:
            logging.info("Starting Heart")
            while not ws.closed:
                await asyncio.sleep(interval / 1000)  # seconds
                logging.info("Sending heartbeat with d <{}>".format(session.getS()))
                await ws.send(json.dumps({
                    "op": 1,  # Heartbeat
                    "d": session.getS()
                }))
        except websockets.exceptions.ConnectionClosedError:
            logging.info("Websocket ConnectionClosedError, Retrying Heartbeat")
        except websockets.exceptions.ConnectionClosedOK:
            logging.info("Websocket was closed, Closing Heartbeat")
        except asyncio.exceptions.CancelledError:
            logging.info("Heartbeat was Cancelled")
        finally:
            logging.info("Closed Heartbeat")

    async def checkTasks(ws, monitors):
        logging.info("Starting SKU Status Checker")
        try:
            while not ws.closed:
                await asyncio.sleep(10)
                logging.info("Checking Monitor Statuses")
                for monitor in monitors:
                    monitor.checkTimestamps()
                # logging.info("Task Checker is Still Running")
        except asyncio.exceptions.CancelledError:
            logging.info("Task Checker was Cancelled")
        finally:
            logging.info("Closed Task Checker")

    async def key_capture():

        # consider implenting signals to propagate a stop webhook to all async subfunctions

        listen = True
        try:
            while listen:
                try:
                    i = await ainput()
                    if i == "q":
                        gateway.status = False
                        listen = False
                except asyncio.TimeoutError:
                    logging.info("Timeout Expired")
        except asyncio.exceptions.CancelledError:
            logging.info("Keylog was Cancelled")
        logging.info("Closed Keylog")

    async def monitor_gateway(url, webhook, channel_id, driver):

        async def watchGateway(websocket):
            while not websocket.closed:
                if not gateway.status:
                    logging.info("Closing Websocket")
                    await websocket.close()
                    break
                await asyncio.sleep(2)

        logging.info("Preparing Monitors")
        sku_monitors = []
        sku_list = []
        with open('skus.txt', "r") as sku_csv:
            csv_reader = csv.reader(sku_csv, delimiter=',')
            for row in csv_reader:
                if row[0] not in sku_list:
                    sku_list.append(row[0])
        sites = ["kidsfootlocker", "champssports", "footaction", "eastbay", "footlocker"]
        for sku in sku_list:
            sku_monitors.append(SKUMonitor(sku, webhook, driver))

        webhook = DiscordWH(webhook_id=credentials["webhook"][33:51], webhook_token=credentials["webhook"][52:])
        logging.info("Started Keylog")
        key = asyncio.create_task(key_capture())

        # connect to socket
        while gateway.status:
            try:
                logging.info("Connecting to Gateway")
                async with websockets.connect("wss://gateway.discord.gg/?v=8&encoding=json") as websocket:
                    watchdog = asyncio.create_task(watchGateway(websocket))
                    async for msg in websocket:
                        data = json.loads(msg)
                        if data["op"] == 10: # hello
                            # set up heartbeat and identify, or attempt to resume
                            heart = asyncio.create_task(heartbeat(websocket, data["d"]["heartbeat_interval"]))
                            task_checker = asyncio.create_task(checkTasks(websocket, sku_monitors))

                            if session.retry:
                                logging.info("Attempting to Resume Session")
                                await websocket.send(json.dumps({
                                    "op": 6, # Resume
                                    "token": credentials["token"],
                                    "session_id": session.getSessionId(),
                                    "seq": session.getS()
                                }))
                            else:
                                logging.info("Sending Identify")
                                await websocket.send(json.dumps({
                                    "op": 2,  # Identify
                                    "d": {
                                        "token": credentials["token"],
                                        "properties": {},
                                        "compress": False,
                                        "large_threshold": 250
                                    }
                                }))
                        elif data["op"] == 11: # heartbeat ack
                            logging.info("Received Heartbeat ACK")

                        # include case when no heartbeat ack is returned, which is zombied or failed connections, to terminate connection

                        elif data["op"] == 7: # reconnect
                            logging.info("Server Reconnect Request, Reconnecting")
                            await websocket.close()

                        elif data["op"] == 9: # invalid session
                            logging.info("Invalid Session, Reidentifying")
                            await websocket.send(json.dumps({
                                "op": 2,  # Identify
                                "d": {
                                    "token": credentials["token"],
                                    "properties": {},
                                    "compress": False,
                                    "large_threshold": 250
                                }
                            }))

                        elif data["op"] == 0: # dispatch
                            if data["t"] == "READY": # ready response, gather session_id
                                logging.info("Retrieving Session ID")
                                session.setSessionId(data["d"]["session_id"])
                            # elif data["t"] == "SESSIONS_REPLACE": # change session_id
                            #     logging.info("Retrieving Session ID")
                            #     session.setSessionId(data["d"][0]["session_id"])
                            elif data["t"] == "MESSAGE_CREATE": # receive message
                                if data["d"]["channel_id"] == channel_id:
                                    timestamp = int(datetime.timestamp(datetime.fromisoformat(data["d"]["timestamp"])) * 1000)
                                    p_url = data["d"]["embeds"][0]["url"]
                                    bot = data["d"]["embeds"][0]["fields"][3]["value"]
                                    for sku_monitor in sku_monitors:
                                        if sku_monitor.getSKU() in p_url:
                                            logging.info("Found message with SKU, Checking Statuses")
                                            for site in sites:
                                                if bot != "KODAI":
                                                    if site == "footlocker":
                                                        if site in p_url and "kids" not in p_url and "footlockerca" not in p_url:
                                                            if sku_monitor.updateTimestamp(timestamp, site):
                                                                for monitor in sku_monitors:
                                                                    monitor.resetStatus()
                                                                    monitor.restartIfStopped()
                                                    else:
                                                        if site in p_url:
                                                            if sku_monitor.updateTimestamp(timestamp, site):
                                                                for monitor in sku_monitors:
                                                                    monitor.resetStatus()
                                                                    monitor.restartIfStopped()
                            logging.info("Setting new S value")
                            session.setS(data["s"])
                            # debug
                            # print(data['t'], data['d'], data["s"])
                            # print(data['d']['channel_id'])

                        else:
                            print(data)
                        
            except websockets.exceptions.ConnectionClosedError:
                logging.info("Connection was closed, restarting socket...")
                session.setSessionId("")
                session.retry = not session.retry
                # TODO need to fix resuming
                await websocket.close()
        terminate(driver=driver, webhook=webhook)
    
    def shutdown(driver):
        driver.close()

    def terminate(driver, webhook):
        logging.info("Stopping Monitor and Closing Tasks")
        if not webhook.send_qt_stopAll_embed():
            logging.info("Failed to send Stop All Webhook")
        if not driver.delete_all_tasks():
            logging.info("Failed to delete all tasks")
        time.sleep(5)
        logging.info("Closing Browser")
        shutdown(driver)

    print("********************************************")
    print("************** KylinQT V1.0.0 **************")
    print("********************************************")
    print("***************By: applearr0w***************")

    # First time setup
    if not path.exists("credentials.json"):
        logging.info("Performing First Time Setup")
        with open('login.json', 'w') as l:
            json.dump({"logged_in":False}, l)
        with open('credentials.json', 'w') as c:
            json.dump({
                "user": "Enter Discord Username/Email",
                "pass": "Enter Discord Password Here",
                "token": "Enter User OAuth Token Here",
                "channel_id": "Enter Channel ID with Log Alerts",
                "webhook": "Enter Webhook Here"
            }, c)
        with open("skus.txt", 'w') as s:
            s.write("Delete this line and add one SKU per line")
        logging.info("Closing, Please Reopen after Setup")
        time.sleep(2)
        return

    while True:
        try:
            # prepare driver
            with open('credentials.json') as c:
                credentials = json.load(c)
            with open('login.json') as login:
                login = json.load(login)

            logging.info("Launching Kylin Dashboard")
            driver = DashboardDriver()
            if not driver.proper_initialize:
                break

            login_success = False
            login_counter = 0
            while not login_success and login_counter < 3:
                if driver.login(login_state=login["logged_in"], user=credentials["user"], pw=credentials["pass"]):
                    logging.info("Successfully logged in")
                    login_success = True
                else:
                    logging.info("Failed to login, retrying")
                    login_counter += 1
            if login_counter > 2:
                logging.info("Unable to login, Closing")
                shutdown(driver=driver)
                break
            
            logging.info("Starting Gateway Connection")
            session = Session()
            webhook = DiscordWH(webhook_id=credentials["webhook"][33:51], webhook_token=credentials["webhook"][52:])

            try:
                asyncio.run((monitor_gateway("wss://gateway.discord.gg/?v=8&encoding=json", webhook=webhook, channel_id=credentials["channel_id"], driver=driver)))
                break
            except KeyboardInterrupt:
                terminate(driver=driver, webhook=webhook)
        except ConnectionRefusedError:
            logging.info("ConnectionRefusedError, Restarting")

class Gateway:
    def __init__(self):
        self.status = True

gateway = Gateway()
runGateway()