import binascii
import can
# can.rc['interface'] = 'socketcan'
# can.rc['channel'] = 'can0'
# can.rc['bitrate'] = 250000
import time
import websockets
import asyncio
import json
import requests
from can import Message
# from can.interface import Bus


class EvengerLogger:

    def __init__(self):
        # busArray = [Bus(
        #     can_filters=[
        #         {"can_id": 0x6b0, "can_mask": 0x1ff, "extended": False}]
        # ), Bus(
        #     can_filters=[
        #         {"can_id": 0x073, "can_mask": 0x1ff, "extended": False}]
        # )]

        self.msg = Message(is_extended_id=False, arbitration_id=1712, data=[
                      0x00, 0x00, 0x03, 0xB6, 0x98, 0x40, 0x40, 0x89])
        self.msg1 = Message(is_extended_id=False, arbitration_id=115, data=[
                       0x29, 0x27, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00])

    def start_logging(self):
        # initialVoltage = int("".join(self.decode_msg(busArray[0].recv())[2:4]), 16) / 10.0
        initialVoltage = int("".join(self.decode_msg(self.msg)[2:4]), 16) / 10.0
        response = requests.post("http://localhost:5000/initialize", data=json.dumps({"initialVoltage": initialVoltage}), headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
        print(response)

        while True:
            # messages = self.busArray[0].recv() + self.busArray[1].recv()
            messageData = self.decode_msg(self.msg) + self.decode_msg(self.msg1)
            self.process_data(messageData)
            time.sleep(.5)
        
    async def sendData(self, body):
        async with websockets.connect("ws://localhost:5000/point") as websocket:
            await websocket.send(body)
            await websocket.close()

    def decode_msg(self, msg):
        data = binascii.hexlify(msg.data)
        bytes0 = [data[i:i+2].decode('utf-8') for i in range(0, len(data), 2)] # May need to remove .decode('utf-8') for the actual messages
        return bytes0

    def process_data(self, data):
        current = int("".join(data[0:2]), 16) / 10.0 # Current is split across bytes 0 & 1
        voltage = int("".join(data[2:4]), 16) / 10.0 # Voltage is split across bytes 2 & 3
        highestCell = int(data[8], 16) / 10.0 # Highest Cell Voltage
        lowestCell = int(data[9], 16) / 10.0 # Lowest Cell Voltage
        averageCell = int(data[10], 16) / 10.0 # Average Cell Voltage

        body = json.dumps({"voltage": voltage, "current": current, "highestCell": highestCell,
                          "lowestCell": lowestCell, "averageCell": averageCell})
        asyncio.get_event_loop().run_until_complete(self.sendData(body))


if __name__ == "__main__":
    logger = EvengerLogger()
    logger.start_logging()
