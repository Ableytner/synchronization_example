import sys

from client import Client
from server import Server

PORT = 21212

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--addr":
        addr = sys.argv[2]

        print(f"Starting server listening on {addr}:{PORT}")
        Server(addr, PORT)
    else:
        print("Starting client")
        addr = input("Please enter the servers address: ")
        usr = input("Please enter your name: ")
        Client(addr, PORT, usr)
