Youming Ding                UNI: yd2611

command for running ChatApp.py:
python3 ChatApp.py -s <port>
python3 ChatApp.py -c <name> <server-ip> <server-port> <client-port>


Project documentation；
There are two class: Server and Client
Server class after initialized will call start() function, which use a while True loop to keep running.
Client class after initialized will start 2 threads for sending and receiving data.

All functions described in handout are realized.

Known bug:
Sometimes the prompt ">>>" will print to different line.