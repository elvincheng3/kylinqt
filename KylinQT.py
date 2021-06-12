import time
import json
from datetime import datetime
import logging
import csv
import websockets
import socket
import asyncio
from os import path
from aioconsole import ainput
from pydispatch import dispatcher

from DashboardDriver import DashboardDriver
from DriverExceptions import LoginError, DriverFailedInitializeError
from GatewayExceptions import HeartFailedError
from Session import Session
from DiscordWH import DiscordWH
from SKUMonitor import SKUMonitor
from QueueData import QueueData

version = "1.1.0"
TEST = False
HEADLESS = True
PAUSE_INTERVAL = 900

logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, handlers=[
    logging.FileHandler("task.log"),
    logging.StreamHandler()
])

SIGNAL_RESUME = 'RESUME'
SIGNAL_LOGIN = 'LOGIN'
site_list = ["footlocker", "champssports", "footaction", "eastbay", "kidsfootlocker"]

def runGateway(test: bool, headless: bool):
    async def heartbeat(ws, interval, session):
        """Send every interval ms the heatbeat message."""
        try:
            while True:
                logging.info("Sending heartbeat with d <{}>".format(session.getS()))
                await ws.send(json.dumps({
                    "op": 1,  # Heartbeat
                    "d": session.getS()
                }))
                await asyncio.sleep(interval / 1000)  # seconds
                if ws.closed:
                    break
        except websockets.exceptions.ConnectionClosedError:
            logging.info("Websocket ConnectionClosedError, Retrying Heartbeat")
        except websockets.exceptions.ConnectionClosedOK:
            logging.info("Websocket was closed, Closing Heartbeat")
        except asyncio.exceptions.CancelledError:
            logging.info("Heartbeat was Cancelled")
        finally:
            logging.info("Closed Heartbeat")

    async def checkTasks(ws, monitors, queue):
        logging.info("Starting SKU Status Checker")
        try:
            while not ws.closed:
                await asyncio.sleep(10)
                logging.info("Checking Monitor Statuses")
                for monitor in monitors:
                    await monitor.checkTimestamps()
        except asyncio.exceptions.CancelledError:
            logging.info("Task Checker was Cancelled")
        finally:
            logging.info("Closed Task Checker")

    async def key_capture():
        try:
            while gateway.status:
                try:
                    i = await ainput()
                    if i == "q":
                        gateway.status = False
                except asyncio.TimeoutError:
                    logging.info("Timeout Expired")
        except asyncio.exceptions.CancelledError:
            logging.info("Keylog was Cancelled")
        logging.info("Closed Keylog")

    async def monitor_gateway(test: bool, url, channel_id, headless):

        async def watchGateway(websocket):
            while not websocket.closed:
                if not gateway.status:
                    logging.info("Closing Websocket")
                    await websocket.close()
                    break
                await asyncio.sleep(2)

        driver_queue = asyncio.Queue()
        driver = DashboardDriver(driver_queue, headless=headless)
        asyncio.create_task(driver.driverManager())
        logging.info("Started Driver Manager")

        if not driver.proper_initialize:
            raise DriverFailedInitializeError

        dispatcher.connect(login_check, signal=SIGNAL_LOGIN, sender=dispatcher.Any)
        await driver_queue.put(QueueData().login(credentials["user"], credentials["pass"]))
        logging.info("Preparing Session and Webhook")
        session = Session()
        webhook = DiscordWH(webhook_id=credentials["webhook"][33:51], webhook_token=credentials["webhook"][52:])
        whitelisted_users = credentials["whitelisted_users"]

        logging.info("Preparing Monitors")
        sku_monitors = []
        sku_list = []
        with open('skus.txt', "r") as sku_csv:
            csv_reader = csv.reader(sku_csv, delimiter=',')
            for row in csv_reader:
                if row[0] not in sku_list:
                    sku_list.append(row[0])
                    monitor = SKUMonitor(row[0], webhook, driver, driver_queue, pause_interval=PAUSE_INTERVAL)
                    sku_monitors.append(monitor)
            logging.info("Started Task Restarters")
        sites = ["kidsfootlocker", "champssports", "footaction", "eastbay", "footlocker"]

        webhook = DiscordWH(webhook_id=credentials["webhook"][33:51], webhook_token=credentials["webhook"][52:])
        logging.info("Started Keylog")
        key = asyncio.create_task(key_capture())

        if test:
            return time.time()

        # connect to socket
        while gateway.status:
            try:
                logging.info("Connecting to Gateway")
                connected = False
                async with websockets.connect("wss://gateway.discord.gg/?v=8&encoding=json", ping_interval=10, ping_timeout=20, max_queue=64, max_size=10000000) as websocket:
                    connected = True
                    watchdog = asyncio.create_task(watchGateway(websocket))
                    async for msg in websocket:
                        data = json.loads(msg)
                        if data["op"] == 10: # hello
                            # set up heartbeat and identify, or attempt to resume
                            heart = asyncio.create_task(heartbeat(websocket, data["d"]["heartbeat_interval"], session))
                            task_checker = asyncio.create_task(checkTasks(websocket, sku_monitors, driver_queue))

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
                            if heart.done():
                                raise HeartFailedError

                        elif data["op"] == 0: # dispatch
                            if data["t"] == "READY": # ready response, gather session_id
                                logging.info("Retrieving Session ID")
                                session.setSessionId(data["d"]["session_id"])
                            elif data["t"] == "MESSAGE_CREATE": # receive message
                                if data["d"]["channel_id"] == channel_id:
                                    # print(data["d"])
                                    logging.info("Detected Footsite Checkout")
                                    timestamp = int(datetime.timestamp(datetime.fromisoformat(data["d"]["timestamp"])) * 1000)
                                    try:
                                        p_url = data["d"]["embeds"][0]["url"]
                                        bot = data["d"]["embeds"][0]["fields"][3]["value"]
                                        for sku_monitor in sku_monitors:
                                            if sku_monitor.getSKU() in p_url:
                                                logging.info("Found message with SKU, Checking Statuses")
                                                for site in sites:
                                                    if bot != "KODAI": # check if ganesh has delayed logs
                                                        if site == "footlocker":
                                                            if site in p_url and "kids" not in p_url and "footlockerca" not in p_url:
                                                                await sku_monitor.updateTimestamp(timestamp, site)
                                                        else:
                                                            if site in p_url:
                                                                await sku_monitor.updateTimestamp(timestamp, site)
                                    except:
                                        logging.info("Error parsing embed, continuing")
                                        logging.info(data["d"])
                                elif data["d"]["author"]["id"] in whitelisted_users:
                                    parsed_query = data["d"]["content"].split()
                                    len_query = len(parsed_query)
                                    if len_query == 1:
                                        if parsed_query[0] == "!help":
                                            logging.info("Received query for help")
                                            webhook.send_qt_receivedHelpQuery()
                                        elif parsed_query[0] == "!stop":
                                            logging.info("Received query to stop quicktasks")
                                            await driver_queue.put(QueueData().stop())
                                            webhook.send_qt_receivedStopQuery()
                                        elif parsed_query[0] == "!quit":
                                            logging.info("Received query to stop KylinQT")
                                            webhook.send_qt_receivedQuitQuery()
                                            gateway.status = False
                                            key.cancel() #TODO: #1 correctly close keylogger after receiving query to quit
                                    elif len_query == 3 and parsed_query[0] == "!start":
                                        if parsed_query[1] in site_list:
                                            logging.info("Received query to start QT with SKU {}".format(parsed_query[2]))
                                            webhook.send_qt_receivedStartQuery(sku=parsed_query[2], site=parsed_query[1])
                                            await driver_queue.put(QueueData().create(sku=parsed_query[2], site=parsed_query[1]))
                                else:
                                    print(data)
                            # logging.info("Setting new S value")
                            session.setS(data["s"])
                            # debug
                            # print(data['t'], data['d'], data["s"])
                            # print(data['d']['channel_id'])

                        else:
                            print(data)
                        
            except websockets.exceptions.ConnectionClosedError:
                logging.info("Connection was closed, Restarting socket...")
                session.setSessionId("")
                session.retry = not session.retry
                await websocket.close()
            except websockets.exceptions.InvalidStatusCode:
                logging.info("Connection was rejected, Restarting socket...")
                session.setSessionId("")
                session.retry = not session.retry
                await websocket.close()
            except HeartFailedError:
                logging.info("Heart Failed Unexpectedly, Restarting Socket")
                session.setSessionId("")
                session.retry = not session.retry
            except socket.gaierror:
                logging.info("Lost connection unexpectedly, Restarting Socket")
                session.setSessionId("")
                session.retry = not session.retry
                time.sleep(.5)
            finally:
                if connected:
                    watchdog.cancel()
                    heart.cancel()
                    task_checker.cancel()
        terminate(driver=driver, webhook=webhook)
    
    def shutdown(driver):
        driver.close()

    def terminate(driver, webhook):
        logging.info("Stopping Monitor and Closing Tasks")
        if not driver.delete_all_tasks():
            logging.info("Failed to delete all tasks")
            if not webhook.failedToStopEmbed():
                logging.info("Failed to send failure webhook")
        if not webhook.send_qt_deleteAll_embed():
            logging.info("Failed to send Stop All Webhook")
        time.sleep(5)
        logging.info("Closing Browser")
        shutdown(driver)

    def login_check(sender, successful):
        if not successful:
            raise LoginError

    print("********************************************")
    print("************** KylinQT V{} **************".format(version))
    print("********************************************")
    print("***************By: applearr0w***************")

    # Test
    if test:
        logging.info("Test Mode")
        start = time.time()
        with open('credentials.json') as c:
            credentials = json.load(c)
        logging.info("Launching Kylin Dashboard")
        end = asyncio.run((monitor_gateway(test=test, url="wss://gateway.discord.gg/?v=8&encoding=json", channel_id=credentials["channel_id"], headless=headless)))
        logging.info("Completed in {}s".format(str(end - start)))
        return

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
                "webhook": "Enter Webhook Here",
                "whitelisted_users": [
                    "Enter user ids that can use user commands"
                ]
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

            logging.info("Launching Kylin Dashboard")
            try:
                asyncio.run((monitor_gateway(test=test, url="wss://gateway.discord.gg/?v=8&encoding=json", channel_id=credentials["channel_id"], headless=headless)))
                break
            except LoginError:
                logging.info("Failed to Login, Exiting")
                gateway.status = False
                break
            except DriverFailedInitializeError:
                logging.info("Failed to Initialize Driver, Exiting")
                gateway.status = False
                break
        except ConnectionRefusedError:
            logging.info("ConnectionRefusedError, Restarting")

class Gateway:
    def __init__(self):
        self.status = True

gateway = Gateway()
runGateway(test=TEST, headless=HEADLESS)