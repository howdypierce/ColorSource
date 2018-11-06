#!/usr/bin/env python3

import socket

SERVER_PORT = 9099
BUF_SIZE = 1024

colors = [(192, 133, 19),
          (181, 18, 27),
          (76, 91, 105),
          (182, 151, 93),
          (0, 120, 255),
          (20, 20, 20)]


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", SERVER_PORT))  # bind to all IP addresses
sock.settimeout(0.1)  # 100 msec

while True:
    try:
        data, client_addr = sock.recvfrom(BUF_SIZE)
        print ("received message: {} from {}".format(data, client_addr))

        if data == b'GET COLOR':
            next_color = colors[0]
            colors = colors[1:]
            colors.append(next_color)

            ret = "COLOR {} {} {}".format(*next_color)
        else:
            ret = "ERROR"

        sent = sock.sendto(ret.encode('utf-8'), client_addr)
        print('sent {} bytes back to {}'.format(sent, client_addr))

    except (socket.timeout):
        # recvfrom timed out
        pass
        
