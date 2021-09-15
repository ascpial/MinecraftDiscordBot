"""This script is comming from https://gist.github.com/Lonami/b09fc1abb471fd0b8b5483d54f737ea0"""

import struct
import socket
import base64
import json
import sys


class Server:
    def __init__(self, data):
        self.description = data.get('description')
        if isinstance(self.description, dict):
            self.description = self.description['text']

        self.icon = base64.b64decode(data.get('favicon', '')[22:])
        self.players = Players(data['players'])
        self.version = data['version']['name']
        self.protocol = data['version']['protocol']

    def __str__(self):
        return 'Server(description={!r}, icon={!r}, version={!r}, '\
                'protocol={!r}, players={})'.format(
            self.description, bool(self.icon), self.version,
            self.protocol, self.players
        )

class Players(list):
    def __init__(self, data):
        super().__init__(Player(x) for x in data.get('sample', []))
        self.max = data['max']
        self.online = data['online']

    def __str__(self):
        return '[{}, online={}, max={}]'.format(
            ', '.join(str(x) for x in self), self.online, self.max
        )

class Player:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']

    def __str__(self):
        return self.name


# For the rest of requests see wiki.vg/Protocol
def ping(ip, port=25565):
    def read_var_int():
        i = 0
        j = 0
        while True:
            k = sock.recv(1)
            if not k:
                return 0
            k = k[0]
            i |= (k & 0x7f) << (j * 7)
            j += 1
            if j > 5:
                raise ValueError('var_int too big')
            if not (k & 0x80):
                return i

    sock = socket.socket()
    sock.connect((ip, port))
    try:
        host = ip.encode('utf-8')
        data = b''  # wiki.vg/Server_List_Ping
        data += b'\x00'  # packet ID
        data += b'\x04'  # protocol variant
        data += struct.pack('>b', len(host)) + host
        data += struct.pack('>H', port)
        data += b'\x01'  # next state
        data = struct.pack('>b', len(data)) + data
        sock.sendall(data + b'\x01\x00')  # handshake + status ping
        length = read_var_int()  # full packet length
        if length < 10:
            if length < 0:
                raise ValueError('negative length read')
            else:
                raise ValueError('invalid response %s' % sock.read(length))

        sock.recv(1)  # packet type, 0 for pings
        length = read_var_int()  # string length
        data = b''
        while len(data) != length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise ValueError('connection abborted')

            data += chunk

        return Server(json.loads(data))
    finally:
        sock.close()

if __name__ == '__main__':
    for sv in sys.argv[1:]:
        print(ping(sv))