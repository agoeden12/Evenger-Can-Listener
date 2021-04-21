import binascii
import can
can.rc['interface'] = 'socketcan'
can.rc['channel'] = 'can0'
can.rc['bitrate'] = 250000
from can.interface import Bus

def process_msg(msg, msg1):
    data = binascii.hexlify(msg.data)
    data1 = binascii.hexlify(msg1.data)

    bytes = [data[i:i+2] for i in range(0, len(data), 2)]
    bytes1 = [data1[i:i+2] for i in range(0, len(data1), 2)]

    print("id: {0} | data: {1}".format(hex(msg.arbitration_id), bytes))
    print("id1: {0} | data1: {1}".format(hex(msg1.arbitration_id), bytes1))

def read_msg():
    bus = Bus()
    bus.set_filters([{"can_id": 0x6b0, "can_mask": 0x1ff, "extended": False}, {"can_id":0x073, "can_mask":0x1ff, "extended":False}])

    while (True):
	msg1 = bus.recv()
        id1 = hex(msg1.arbitration_id)
        msg = bus.recv()
        if (id1 == "0x6b0"):
            process_msg(msg1, msg)
        else:
            process_msg(msg, msg1)

if __name__ == "__main__":
   read_msg()
