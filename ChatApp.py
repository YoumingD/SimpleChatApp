import sys
import socket
import threading
import os
import json
import time
import datetime
import signal


class Server:
    def __init__(self, port):
        self.port = port
        self.saved_msg = []
        self.saved_all = []
        self.table = []
        # get ip address
        ip_address = socket.gethostbyname(socket.gethostname())
        # create socket and bind ip address and port to this socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((ip_address, self.port))
        print("[Server started. ip is {}. port is {}.]".format(ip_address, port))

    def start(self):
        while True:
            try:
                # receive requests from client
                pkt = self.server.recvfrom(4096)
                pair = pkt[1]
                p = pkt[0].decode("utf-8")
                json_obj = json.loads(p)
                type = json_obj.get('type')

                # the registration request
                if type == "REG":
                    name = json_obj.get('msg')
                    address = pkt[1][0]
                    port = int(pkt[1][1])
                    flag = False
                    has_info = False
                    has_save = False
                    exist = False
                    for i in range(len(self.table)):
                        n = self.table[i][0]
                        if name == n:
                            # change status from No to Yes
                            if self.table[i][3] == "No":
                                y = list(self.table[i])
                                y[3] = "Yes"
                                self.table[i] = tuple(y)
                                flag = True
                            # duplicated registration case
                            else:
                                msg_tosend = "[Client <{}> exists!!]".format(name)
                                request = {"type": "MESSAGE", "msg": msg_tosend}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.server.sendto(data, pair)
                                exist = True
                    if exist:
                        continue
                    # new client
                    if not flag:
                        self.table.append((name, address, port, "Yes"))
                    else:
                        for i in range(len(self.saved_msg)):
                            n = self.saved_msg[i][1]
                            if name == n:
                                has_info = True
                        for i in range(len(self.saved_all)):
                            n = self.saved_all[i][1]
                            if name == n:
                                has_save = True

                    msg_tosend = "[Welcome, You are registered.]"
                    request = {"type": "MESSAGE", "msg": msg_tosend}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.server.sendto(data, pair)

                    f = False

                    # send client saved channel msg if there is any
                    index2 = []
                    if has_save:
                        msg_tosend = "[You Have Messages.]"
                        request = {"type": "MESSAGE", "msg": msg_tosend}
                        json_string = json.dumps(request)
                        data = json_string.encode("utf-8")
                        self.server.sendto(data, pair)

                        for i in range(len(self.saved_all)):
                            n = self.saved_all[i][1]
                            if name == n:
                                msg_tosend = "[Channel-Message client " + self.saved_all[i][0] + ": " + \
                                             self.saved_all[i][3] + " " \
                                             + self.saved_all[i][2] + "]"
                                request = {"type": "MESSAGE", "msg": msg_tosend}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.server.sendto(data, pair)
                                index2.append(self.saved_all[i])

                        for i in range(len(index2)):
                            self.saved_all.remove(index2[i])

                        f = True

                    # send client saved msg if there is any
                    if has_info:
                        if not f:
                            msg_tosend = "[You Have Messages.]"
                            request = {"type": "MESSAGE", "msg": msg_tosend}
                            json_string = json.dumps(request)
                            data = json_string.encode("utf-8")
                            self.server.sendto(data, pair)

                        index = []
                        for i in range(len(self.saved_msg)):
                            n = self.saved_msg[i][1]
                            if name == n:
                                msg_tosend = "[Client " + self.saved_msg[i][0] + ": " + self.saved_msg[i][3] + " " \
                                             + self.saved_msg[i][2] + "]"
                                request = {"type": "MESSAGE", "msg": msg_tosend}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.server.sendto(data, pair)
                                index.append(self.saved_msg[i])

                        for i in range(len(index)):
                            self.saved_msg.remove(index[i])

                    # send updated client table to all clients
                    for t in self.table:
                        addr = t[1]
                        p = t[2]
                        if t[3] == "Yes":
                            request = {"type": "TABLE", "msg": self.table}
                            json_string = json.dumps(request)
                            data = json_string.encode("utf-8")
                            self.server.sendto(data, (addr, p))

                            msg_tosend = "[Client table updated.]"
                            request = {"type": "MESSAGE", "msg": msg_tosend}
                            json_string = json.dumps(request)
                            data = json_string.encode("utf-8")
                            self.server.sendto(data, (addr, p))
                # de-registration request
                elif type == "DEREG":
                    name = json_obj.get('msg')
                    # change the status of client from Yes to No
                    for i in range(len(self.table)):
                        n = self.table[i][0]
                        if name == n:
                            y = list(self.table[i])
                            y[3] = "No"
                            self.table[i] = tuple(y)
                    # send ACK to client
                    request = {"type": "ACK_D", "msg": ""}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.server.sendto(data, pair)

                    # update table and send new table to all online clients
                    for t in self.table:
                        addr = t[1]
                        p = t[2]
                        if t[3] == "Yes":
                            request = {"type": "TABLE", "msg": self.table}
                            json_string = json.dumps(request)
                            data = json_string.encode("utf-8")
                            self.server.sendto(data, (addr, p))

                            msg_tosend = "[Client table updated.]"
                            request = {"type": "MESSAGE", "msg": msg_tosend}
                            json_string = json.dumps(request)
                            data = json_string.encode("utf-8")
                            self.server.sendto(data, (addr, p))
                # save message request
                elif type == "SAVE":
                    # save the message with sender, receiver, timestamp
                    info = json_obj.get('msg')
                    n1 = json_obj.get('sender_name')
                    n2 = json_obj.get('rec_name')
                    now = datetime.datetime.now()
                    time = now.strftime("%Y-%m-%d %H:%M:%S")
                    self.saved_msg.append((n1, n2, info, time))

                    # send ACK
                    msg_tosend = ">>> [Messages received by the server and saved.]"
                    request = {"type": "ACK_SAVE", "msg": msg_tosend}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.server.sendto(data, pair)
                # save channel message request
                elif type == "SEND_ALL":
                    # send ACK
                    request = {"type": "ACK_A", "msg": ""}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.server.sendto(data, pair)

                    # save message with sender, receiver, timestamp for all offline clients
                    msg = json_obj.get('msg')
                    name = json_obj.get('name')
                    update = False
                    for i in range(len(self.table)):
                        n = self.table[i][0]
                        if name != n:
                            if self.table[i][3] == "Yes":
                                m = "[Channel-Message client " + name + ": " + msg + "]"
                                request = {"type": "CHANNEL", "msg": m}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.server.sendto(data, (self.table[i][1], self.table[i][2]))
                                try:
                                    self.server.settimeout(0.5)
                                    pkt = self.server.recvfrom(4096)
                                    pair = pkt[1]
                                    p = pkt[0].decode("utf-8")
                                    json_obj = json.loads(p)
                                    type = json_obj.get('type')
                                    if type == "ACK":
                                        continue
                                except socket.timeout:
                                    # if timeout, change the status of client to No.
                                    update = True
                                    if self.table[i][3] == "Yes":
                                        y = list(self.table[i])
                                        y[3] = "No"
                                        self.table[i] = tuple(y)

                                        now = datetime.datetime.now()
                                        time = now.strftime("%Y-%m-%d %H:%M:%S")
                                        self.saved_all.append((name, self.table[i][0], msg, time))
                            else:
                                now = datetime.datetime.now()
                                time = now.strftime("%Y-%m-%d %H:%M:%S")
                                self.saved_all.append((name, self.table[i][0], msg, time))
                    self.server.settimeout(100000)
                    # update table and send new table to all online clients
                    if update:
                        for t in self.table:
                            addr = t[1]
                            p = t[2]
                            if t[3] == "Yes":
                                request = {"type": "TABLE", "msg": self.table}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.server.sendto(data, (addr, p))

                                msg_tosend = "[Client table updated.]"
                                request = {"type": "MESSAGE", "msg": msg_tosend}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.server.sendto(data, (addr, p))
            # handle silent leave
            except (KeyboardInterrupt, SystemExit) as error:
                self.server.close()
                os._exit(1)


ack_flag = False
ackd_flag = False
acka_flag = False
exit_flag = False
save_flag = False


class Client:
    def __init__(self, name, host_ip, host_port, client_port):
        try:
            # create client socket with given port number
            self.table = []
            self.username = name
            self.server_address = host_ip
            self.server_port = int(host_port)
            self.client_port = int(client_port)
            ip_address = socket.gethostbyname(socket.gethostname())
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((ip_address, self.client_port))

            # send registration request to server at first
            request = {"type": "REG", "msg": name}
            json_string = json.dumps(request)
            data = json_string.encode("utf-8")
            self.socket.sendto(data, (self.server_address, self.server_port))
            # receive ACK from server
            pkt = self.socket.recvfrom(4096)
            receive_msg = pkt[0].decode("utf-8")
            json_obj = json.loads(receive_msg)
            m = json_obj.get('msg')
            print(">>> " + m)
            # start receive and send threads
            t1 = threading.Thread(target=self.send)
            t2 = threading.Thread(target=self.receive)
            t1.setDaemon(True)
            t2.setDaemon(True)
            t1.start()
            t2.start()
            # handle silent leave
            signal.signal(signal.SIGINT, self.my_sig_handler)
            while True:
                if exit_flag:
                    break
        # handle silent leave
        except KeyboardInterrupt:
            self.socket.close()
            sys.exit(0)

    def my_sig_handler(sig, frame, frame2):
        sys.exit(0)

    def send(self):
        global ack_flag
        global ackd_flag
        global acka_flag
        global exit_flag
        global save_flag
        while True:
            try:
                x = input(">>> ")
                commend = x.split()
                # send command
                if commend[0] == "send":
                    for i in range(len(self.table)):
                        if self.table[i][0] == commend[1]:
                            str = ""
                            for k in range(2, len(commend) - 1):
                                str = str + commend[k] + " "
                            str = str + commend[len(commend) - 1]
                            # send message if the receiver is online
                            if self.table[i][3] == "Yes":
                                ack_flag = False
                                request = {"type": "CHAT", "msg": str, "sender": self.username}
                                json_string = json.dumps(request)
                                data = json_string.encode("utf-8")
                                self.socket.sendto(data, (self.table[i][1], self.table[i][2]))
                                time.sleep(0.5)
                                # if no ACK, send msg to server after 5 times tries
                                if not ack_flag:
                                    print(">>> [No ACK from <{}>, message sent to server.]".format(self.table[i][0]))

                                    count = 5
                                    exit_flag = False
                                    save_flag = False
                                    while count > 0:
                                        count = count - 1
                                        request = {"type": "SAVE", "msg": str, "sender_name": self.username,
                                                   "rec_name": self.table[i][0]}
                                        json_string = json.dumps(request)
                                        data = json_string.encode("utf-8")
                                        self.socket.sendto(data, (self.server_address, self.server_port))
                                        time.sleep(0.5)
                                        if save_flag:
                                            break
                                    # if server no respond, exit
                                    if not save_flag:
                                        print(">>> [Server not responding]")
                                        print(">>> [Exiting]")
                                        exit_flag = True
                                        sys.exit(0)
                            # if receiver is offline, directly send to server
                            else:
                                print(">>> [No ACK from <{}>, message sent to server.]".format(self.table[i][0]))

                                count = 5
                                exit_flag = False
                                save_flag = False
                                while count > 0:
                                    count = count - 1
                                    request = {"type": "SAVE", "msg": str, "sender_name": self.username,
                                               "rec_name": self.table[i][0]}
                                    json_string = json.dumps(request)
                                    data = json_string.encode("utf-8")
                                    self.socket.sendto(data, (self.server_address, self.server_port))
                                    time.sleep(0.5)
                                    if save_flag:
                                        break
                                # if server no respond after 5 times timeout, exit
                                if not save_flag:
                                    print(">>> [Server not responding]")
                                    print(">>> [Exiting]")
                                    exit_flag = True
                                    sys.exit(0)
                # de-registration command
                if commend[0] == "dereg":
                    count = 5
                    ackd_flag = False
                    while count > 0:
                        count = count - 1
                        request = {"type": "DEREG", "msg": commend[1]}
                        json_string = json.dumps(request)
                        data = json_string.encode("utf-8")
                        self.socket.sendto(data, (self.server_address, self.server_port))
                        time.sleep(0.5)
                        if ackd_flag:
                            break
                    # if tried 5 times no respond from server, exit
                    if not ackd_flag:
                        print(">>> [Server not responding]")
                        print(">>> [Exiting]")
                        exit_flag = True
                        sys.exit(0)
                # registration command
                if commend[0] == "reg":
                    request = {"type": "REG", "msg": commend[1]}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.socket.sendto(data, (self.server_address, self.server_port))
                # send_all command
                if commend[0] == "send_all":
                    count = 5
                    acka_flag = False
                    while count > 0:
                        count = count - 1
                        str = ""
                        for k in range(1, len(commend) - 1):
                            str = str + commend[k] + " "
                        str = str + commend[len(commend) - 1]
                        request = {"type": "SEND_ALL", "msg": str, "name": self.username}
                        json_string = json.dumps(request)
                        data = json_string.encode("utf-8")
                        self.socket.sendto(data, (self.server_address, self.server_port))
                        time.sleep(0.5)
                        if acka_flag:
                            break
                    # if no ack from server in 500 msecs, print [Server not responding]
                    if not acka_flag:
                        print(">>> [Server not responding]")
            except KeyboardInterrupt:
                break

    def receive(self):
        global ack_flag
        global ackd_flag
        global acka_flag
        global save_flag
        while True:
            try:
                # receive data from other client or server
                pkt = self.socket.recvfrom(4096)
                pair = pkt[1]
                p = pkt[0].decode("utf-8")
                json_obj = json.loads(p)
                type = json_obj.get('type')
                # the table data, update the current table to new table
                if type == "TABLE":
                    self.table = json_obj.get('msg')
                # the message data, print data and send back ACK
                elif type == "MESSAGE":
                    msg = json_obj.get('msg')
                    print(msg + "\n" + ">>> ", end="")
                    request = {"type": "ACK", "msg": self.username}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.socket.sendto(data, pair)
                # ACK data
                elif type == "ACK":
                    ack_flag = True
                    name = json_obj.get('msg')
                    print(">>> [Message received by <{}>.]".format(name))
                # ACK for de-registration
                elif type == "ACK_D":
                    ackd_flag = True
                    print(">>> [You are Offline. Bye.]")
                # ACK for channel msg
                elif type == "ACK_A":
                    acka_flag = True
                    print(">>> [Message received by Server.]")
                # channel message data, send back ack
                elif type == "CHANNEL":
                    msg = json_obj.get('msg')
                    print(msg + "\n" + ">>> ", end="")
                    request = {"type": "ACK", "msg": self.username}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.socket.sendto(data, pair)
                # chat data, send back ACK
                elif type == "CHAT":
                    msg = json_obj.get('msg')
                    n = json_obj.get('sender')
                    print("[Client " + n + ": " + msg + "]\n" + ">>> ", end="")
                    request = {"type": "ACK", "msg": self.username}
                    json_string = json.dumps(request)
                    data = json_string.encode("utf-8")
                    self.socket.sendto(data, pair)
                # ACK for save
                elif type == "ACK_SAVE":
                    msg = json_obj.get('msg')
                    print(msg + "\n" + ">>> ", end="")
                    save_flag = True
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Instruction:", "[python ChatApp -s <port>]",
              "[python ChatApp -c <name> <server-ip> <server-port> <client-port>]", sep="  ")
        sys.exit()
    mode = sys.argv[1]
    # server mode
    if mode == "-s":
        if len(sys.argv) != 3:
            print("Instruction:    [python ChatApp -s <port>]")
            sys.exit()
        port = int(sys.argv[2])
        # check for port validity
        if port < 1024:
            print("[port must in range 1024-65535.]")
            sys.exit()
        if port > 65535:
            print("[port must in range 1024-65535.]")
            sys.exit()
        server = Server(port)
        server.start()
    # client mode
    elif mode == "-c":
        if len(sys.argv) != 6:
            print("Instruction:    [python ChatApp -c <name> <server-ip> <server-port> <client-port>]")
            sys.exit()
        name = sys.argv[2]
        server_ip = sys.argv[3]
        server_port = int(sys.argv[4])
        client_port = int(sys.argv[5])
        # check for IP validity
        temp = server_ip.split(".")
        if len(temp) != 4:
            print("[IP address is not valid.]")
            sys.exit()
        for t in temp:
            if not t.isnumeric():
                print("[IP address is not valid.]")
                sys.exit()
            if not 0 <= int(t) <= 255:
                print("[IP address is not valid.]")
                sys.exit()
        # check for port validity
        if server_port < 1024:
            print("[port must in range 1024-65535.]")
            sys.exit()
        if server_port > 65535:
            print("[port must in range 1024-65535.]")
            sys.exit()
        if client_port < 1024:
            print("[port must in range 1024-65535.]")
            sys.exit()
        if client_port > 65535:
            print("[port must in range 1024-65535.]")
            sys.exit()
        client = Client(name, server_ip, server_port, client_port)
    else:
        print("Instruction:", "[python ChatApp -s <port>]",
              "[python ChatApp -c <name> <server-ip> <server-port> <client-port>]", sep="  ")
        sys.exit()
