import binascii
import can
import time
import websockets, asyncio, json
import requests
from can import Message

class EvengerLogger:

    async def sendData(self, body):
        async with websockets.connect("ws://localhost:5000/point") as websocket:
                await websocket.send(body)
                response = await websocket.recv()
                print(response)

    def process_msg(self, msg, msg1):
        data = binascii.hexlify(msg.data)
        data1 = binascii.hexlify(msg1.data)
        
        bytes0 = [data[i:i+2].decode('utf-8') for i in range(0, len(data), 2)]
        bytes1 = [data1[i:i+2].decode('utf-8') for i in range(0, len(data1), 2)]

        currentBytes = (bytes0[0] + bytes0[1])
        current = int(currentBytes, 16) / 10.0

        voltageBytes = (bytes0[2] + bytes0[3])
        voltage = int(voltageBytes, 16) / 10.0

        highestCell = int(bytes1[0], 16) / 10.0
        lowestCell = int(bytes1[1], 16) / 10.0
        averageCell = int(bytes1[2], 16) / 10.0

        body = json.dumps({"voltage": voltage, "current": current, "highestCell": highestCell, "lowestCell": lowestCell, "averageCell": averageCell})
        asyncio.get_event_loop().run_until_complete(self.sendData(body))

        # print("voltage: {0} | current: {1} | highestCell: {2} | lowestCell: {3} | averageCell: {4}".format(voltage, current, highestCell, lowestCell, averageCell))

        # print("id: {0} | data: {1}".format(hex(msg.arbitration_id), bytes0))
        # print("id1: {0} | data1: {1}".format(hex(msg1.arbitration_id), bytes1))

    def read_msg(self):
        # bus = Bus()
        # bus.set_filters([{"can_id": 0x6b0, "can_mask": 0x1ff, "extended": False}, {"can_id":0x073, "can_mask":0x1ff, "extended":False}])

        msg = Message(is_extended_id=False, arbitration_id=1712, data=[0x00,0x00,0x03,0xB6,0x98,0x40,0x40,0x89])
        msg1 = Message(is_extended_id=False, arbitration_id=115, data=[0x29,0x27,0x28,0x00,0x00,0x00,0x00,0x00])

        while (True):
            self.process_msg(msg, msg1)
            time.sleep(.5)
            
        # msg1 = bus.recv()
        #     id1 = hex(msg1.arbitration_id)
        #     msg = bus.recv()
        #     if (id1 == "0x6b0"):
        #         self.process_msg(msg1, msg)
        #     else:
        #         self.process_msg(msg, msg1)

if __name__ == "__main__":
    response = requests.post("http://localhost:5000/initialize")
    print(response)

    logger = EvengerLogger()
    logger.read_msg()
