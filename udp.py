import socket
import json
from WebApp import receive

def broadcast(content):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    network = '<broadcast>'
    s.sendto(json.dumps(content).encode('utf-8'), (network, port))
    s.close()


def listen():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    s.bind(('', port))
    print('Listening for broadcast at ', s.getsockname())

    while True:
        data, address = s.recvfrom(65535)
        print('Server received from {}:{}'.format(address, data.decode('utf-8')))



