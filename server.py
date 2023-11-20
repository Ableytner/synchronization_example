import re
import sys
import os

from socket import create_connection
from socketserver import ThreadingTCPServer, BaseRequestHandler
from threading import Lock, Thread
from time import sleep

from list_utils import str_to_list, unify_lists

class Server():
    def __init__(self, addr: str, port: int) -> None:
        self._conn_tuple = (addr, port)
        self._socketserver = ThreadingTCPServer(self._conn_tuple, TCPClientHandler)
        self.the_list: list[tuple[str, str, str, float]] = []

        self._servers = []
        self._serversync_thread = Thread(target=self.serversync_func, daemon=True)
        self._serversync_thread.start()

        Server.instance = self
        Server.lock = Lock()

        self._socketserver.serve_forever()

    instance = None
    lock = None

    def serversync_func(self):
        if not os.path.isfile("servers.txt"):
            with open("servers.txt", "w+"):
                pass
        
        with open("servers.txt", "r") as f:
            for addr in f.readlines():
                if re.match(r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$", addr):
                    self._servers.append(addr.strip())
        
        while True:
            for addr in self._servers:
                try:
                    # send local database
                    sock = create_connection((addr, self._conn_tuple[1]))
                    self._send(sock, f"PUT db {self.the_list}")
                    assert self._recv(sock) == "ACK"

                    # receive remote database
                    sock = create_connection((addr, self._conn_tuple[1]))
                    self._send(sock, "GET db")
                    new_list = str_to_list(self._recv(sock))
                    self.sync_list(new_list)
                # ignore the server if it is offline
                except (TimeoutError, ConnectionRefusedError):
                    pass

            sleep(10)

    def sync_list(self, new_list: list[tuple[str, str, float]]):
        old_hash = hash(tuple(self.the_list))

        with self.lock:
            self.the_list = unify_lists(self.the_list, new_list)
        
        # redraw screen if the_list has changed
        if hash(tuple(self.the_list)) != old_hash:
            self.redraw_screen()

    def redraw_screen(self):
        ID_LEN = 6
        USR_LEN = 16
        MSG_LEN = 96

        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")
        print("-" * (USR_LEN + MSG_LEN))
        print(f"ID{' ' * (ID_LEN - 2)}USER{' ' * (USR_LEN - 4)}MESSAGE{' ' * (MSG_LEN - 7)}")
        for c, item in enumerate(self.the_list):
            print(f"{c}{' ' * (ID_LEN - len(str(c)))}{item[2][:USR_LEN]}{' ' * (USR_LEN - len(item[2]))}{item[1][:MSG_LEN]}{' ' * (MSG_LEN - len(item[1]))}")
        print("-" * (USR_LEN + MSG_LEN))

    def _send(self, sock, text):
        """Send a string to the given socket"""

        sock.send(self._string_to_bytes(text))

    def _recv(self, sock):
        """Receive a string from the given socket"""

        return self._bytes_to_string(sock.recv(4096))

    @staticmethod
    def _string_to_bytes(input_text):
        """Convert a string to a bytes object"""

        return bytes(input_text, 'utf-8')

    @staticmethod
    def _bytes_to_string(input_bytes):
        """Convert a bytes object to a string"""

        return input_bytes.decode()

class TCPClientHandler(BaseRequestHandler):
    def handle(self) -> None:
        # print(f"Received message from {self.client_address}")

        req = orig_req = self.receive_text()

        spl = req.split(" ", maxsplit=1)
        if len(spl) == 1:
            req_type = spl[0]
        else:
            req_type, req = spl

        match req_type:
            case "PING":
                self.send_text("ACK")
                return
            
            case "GET":
                spl = req.split(" ", maxsplit=1)
                if len(spl) == 1:
                    get_type = spl[0]
                else:
                    get_type, req = spl

                if get_type == "db":
                    self.send_text(repr(Server.instance.the_list))
                    return

            case "PUT":
                req_type, req = req.split(" ", maxsplit=1)
                if req_type == "db":

                    conv_req = str_to_list(req)

                    Server.instance.sync_list(conv_req)

                    self.send_text("ACK")
                    return

        raise Exception(f"Could not process request {orig_req}")

    def send_text(self, text: str):
        """Send string to the given socket"""

        self.request.sendall(self._string_to_bytes(text))

    def receive_text(self) -> str:
        """Receive string from the given socket"""

        return self._bytes_to_string(self.request.recv(65536))

    @staticmethod
    def _string_to_bytes(input_text):
        """Convert string to bytes object"""

        return bytes(input_text, 'utf-8')

    @staticmethod
    def _bytes_to_string(input_bytes):
        """Convert bytes object to string"""

        return input_bytes.decode()
