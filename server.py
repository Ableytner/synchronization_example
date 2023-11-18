from socketserver import ThreadingTCPServer, BaseRequestHandler
from threading import Lock

from list_utils import str_to_list, unify_lists

class Server():
    def __init__(self, addr: str, port: int) -> None:
        self._conn_tuple = (addr, port)
        self._socketserver = ThreadingTCPServer(self._conn_tuple, TCPClientHandler)
        self.the_list: list[tuple[str, str, str, float]] = []

        Server.instance = self
        Server.lock = Lock()

        self._socketserver.serve_forever()

    instance = None
    lock = None

    def sync_list(self, new_list: list[tuple[str, str, float]]):
        with self.lock:
            self.the_list = unify_lists(self.the_list, new_list)
            return

            uids = [item[0] for item in self.the_list]

            for line in new_list:
                # the element already exists
                if line in self.the_list:
                    continue

                # the element is new
                if line[0] not in uids:
                    self.the_list.append(line)
                    uids = [item[0] for item in self.the_list]
                    continue

                # the element has changed
                if line[0] in uids:
                    curr_line = self.the_list[uids.index(line[0])]

                    # the current element is newer
                    if curr_line[3] > line[3]:
                        continue

                    # the new element is newer
                    self.the_list[uids.index(line[0])] = line
                    uids = [item[0] for item in self.the_list]

class TCPClientHandler(BaseRequestHandler):
    def handle(self) -> None:
        print(f"Received message from {self.client_address}")

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
                    print(req)

                    conv_req = str_to_list(req)
                    print(conv_req)

                    Server.instance.sync_list(conv_req)
                    print(Server.instance.the_list)

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
