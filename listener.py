import binascii
import can
can.rc['interface'] = 'socketcan'
can.rc['channel'] = 'can0'
can.rc['bitrate'] = 250000
import time
import websockets
import asyncio
import json
import requests
from can import Message
from can.interface import Bus


class EvengerLogger:

    def __init__(self):
        # Store the filtered CAN busses for the specific message IDs set on the go-kart
        self.busArray = [Bus(
            can_filters=[
                {"can_id": 0x6b0, "can_mask": 0x1ff, "extended": False}]
        ), Bus(
            can_filters=[
                {"can_id": 0x073, "can_mask": 0x1ff, "extended": False}]
        )]

    def start_logging(self):
        # Collect initial data that will be used to initialize and start a session
        initialVoltage = int("".join(self.decode_msg(self.busArray[0].recv())[2:4]), 16) / 10.0
        response = requests.post("http://localhost:5000/initialize", data=json.dumps(
            {"initialVoltage": initialVoltage}), headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
        print(response)

        # Infinitely loop through collecting messages and combining them before decoding the hex data and sending to the websocket
        while True:
            messages = self.decode_msg(self.busArray[0].recv()) + self.decode_msg(self.busArray[1].recv())
            self.process_data(messages)
            
            # Set the loop to wait for 500ms since each message is configured to be sent every 500ms
            # conserving precious computing power for the rest of the systems
            time.sleep(.5)

    async def sendData(self, body):
        # Asynchronously send the message over the websocket to not prevent the script getting held up
        async with websockets.connect("ws://localhost:5000/point") as websocket:
            await websocket.send(body)
            response = await websocket.recv()
            await websocket.close()

    def decode_msg(self, msg):
        # Convert the bytes from the CAN bus into Hex data as a string and return as a array of Hex strings
        data = binascii.hexlify(msg.data)
        bytes0 = [data[i:i+2].decode('utf-8') for i in range(0, len(data), 2)]
        return bytes0

    def process_data(self, data):
        # Current is split across bytes 0 & 1
        current = int("".join(data[0:2]), 16) / 10.0
        # Voltage is split across bytes 2 & 3
        voltage = int("".join(data[2:4]), 16) / 10.0
        highestCell = int(data[8], 16) / 10.0  # Highest Cell Voltage
        lowestCell = int(data[9], 16) / 10.0  # Lowest Cell Voltage
        averageCell = int(data[10], 16) / 10.0  # Average Cell Voltage

        # Form the JSON object to be sent over the websocket to the Middleware
        body = json.dumps({"voltage": voltage, "current": current, "highestCell": highestCell,
                          "lowestCell": lowestCell, "averageCell": averageCell})
        asyncio.get_event_loop().run_until_complete(self.sendData(body))


if __name__ == "__main__":
    # Initialize the class and any class variables
    logger = EvengerLogger()

    # Start reading messages from the CAN bus and transmit them to the Websocket
    logger.start_logging()
