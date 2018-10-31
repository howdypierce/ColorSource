#!/usr/bin/env python3
#
# Super-simple client, to test the server
#
# Usage: color-client.py arg arg arg...
#
# The ASCII message specified by concatenating the arguments will be
# sent to the server, and then the client will wait for a response,
# which will be printed to stdout

import socket
import sys

SERVER_IP = 'color-source.local'
SERVER_PORT = 9099
BUF_SIZE = 1024

message = " ".join(sys.argv[1:])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
sock.sendto(message.encode('utf-8'), (SERVER_IP, SERVER_PORT))

data, server = sock.recvfrom(BUF_SIZE)
print('received {}'.format(data))
