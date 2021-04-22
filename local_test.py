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

        msg = Message(is_extended_id=False, arbitration_id=1712, data=[
                      0x00, 0x00, 0x03, 0xB6, 0x98, 0x40, 0x40, 0x89])
        msg1 = Message(is_extended_id=False, arbitration_id=115, data=[
                       0x29, 0x27, 0x28, 0x00, 0x00, 0x00, 0x00, 0x00])

        while True:
            # messages = busArray[0].recv() + busArray[1].recv()
            messageData = self.decode_msg(msg) + self.decode_msg(msg1)
            self.process_data(messageData)
            time.sleep(.5)

    async def sendData(self, body):
        async with websockets.connect("ws://localhost:5000/point") as websocket:
            await websocket.send(body)
            await websocket.close()

    def decode_msg(self, msg):
        data = binascii.hexlify(msg.data)
        bytes0 = [data[i:i+2].decode('utf-8') for i in range(0, len(data), 2)]
        return bytes0

    def process_data(self, data):
        currentBytes = (data[0] + data[1])
        current = int(currentBytes, 16) / 10.0

        voltageBytes = (data[2] + data[3])
        voltage = int(voltageBytes, 16) / 10.0

        highestCell = int(data[8], 16) / 10.0
        lowestCell = int(data[9], 16) / 10.0
        averageCell = int(data[10], 16) / 10.0

        body = json.dumps({"voltage": voltage, "current": current, "highestCell": highestCell,
                          "lowestCell": lowestCell, "averageCell": averageCell})
        asyncio.get_event_loop().run_until_complete(self.sendData(body))


if __name__ == "__main__":
    initialVoltage = 98
    response = requests.post("http://localhost:5000/initialize", data=json.dumps(
        {"initialVoltage": initialVoltage}), headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
    print(response)

    logger = EvengerLogger()
