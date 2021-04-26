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
        self.busArray = [Bus(
            can_filters=[
                {"can_id": 0x6b0, "can_mask": 0x1ff, "extended": False}]
        ), Bus(
            can_filters=[
                {"can_id": 0x073, "can_mask": 0x1ff, "extended": False}]
        )]

    def start_logging(self):
        initialVoltage = int("".join(self.decode_msg(self.busArray[0].recv())[2:4]), 16) / 10.0
        response = requests.post("http://localhost:5000/initialize", data=json.dumps(
            {"initialVoltage": initialVoltage}), headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
        print(response)

        while True:
            messages = self.decode_msg(self.busArray[0].recv()) + self.decode_msg(self.busArray[1].recv())
            self.process_data(messages)
            time.sleep(.5)

    async def sendData(self, body):
        async with websockets.connect("ws://localhost:5000/point") as websocket:
            await websocket.send(body)
            response = await websocket.recv()
            await websocket.close()

    def decode_msg(self, msg):
        data = binascii.hexlify(msg.data)
        # May need to remove .decode('utf-8') for the actual messages
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

        body = json.dumps({"voltage": voltage, "current": current, "highestCell": highestCell,
                          "lowestCell": lowestCell, "averageCell": averageCell})
        asyncio.get_event_loop().run_until_complete(self.sendData(body))


if __name__ == "__main__":
    logger = EvengerLogger()
    logger.start_logging()
