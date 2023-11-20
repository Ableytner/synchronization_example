from datetime import datetime
from socket import create_connection
from threading import Thread
from time import sleep

from list_utils import str_to_list, unify_lists

class Client:
    def __init__(self, addr: str, port: int, username: str, autosync: bool = True) -> None:
        self._conn_tuple = (addr, port)
        self.the_list = []

        self._keepalive_thread = Thread(target=self.keepalive_func, daemon=True)
        self._keepalive_thread.start()

        if autosync:
            self._autosync_thread = Thread(target=self.autosync_func, daemon=True)
            self._autosync_thread.start()
            # wait for the sync to finish
            sleep(0.5)

        self.username = username

        self.cli()

    def cli(self):
        ID_LEN = 6
        USR_LEN = 16
        MSG_LEN = 112
        exit = False

        while not exit:
            print("-" * (USR_LEN + MSG_LEN))
            print(f"ID{' ' * (ID_LEN - 2)}USER{' ' * (USR_LEN - 4)}MESSAGE{' ' * (MSG_LEN - 7)}")
            for c, item in enumerate(self.the_list):
                print(f"{c}{' ' * (ID_LEN - len(str(c)))}{item[2][:USR_LEN]}{' ' * (USR_LEN - len(item[2]))}{item[1][:MSG_LEN]}{' ' * (MSG_LEN - len(item[1]))}")
            print("-" * (USR_LEN + MSG_LEN))

            uin = input("> ").strip()

            match uin:
                case "exit" | "quit" | "stop" | "q":
                    exit = True
                case "help" | "h":
                    self.print_help()
                case "get" | "load" | "pull":
                    self.get_database()
                case "post" | "put" | "push" |"commit":
                    self.send_database()
                case "update" | "sync":
                    self.get_database()
                    self.send_database()
                case "send" | "new" | "message" | "msg":
                    self.create_message()
                case "edit" | "change":
                    self.edit_message()

    def print_help(self):
        """Print out a help message"""

        cmds = {
            "exit the program": ("exit", "quit", "stop", "q"),
            "print this text": ("help", "h"),
            "pull remote changes": ("get", "load", "pull"),
            "push local changes": ("post", "put", "push", "commit"),
            "pull and push changes": ("update", "sync"),
            "create a new message": ("send", "new", "message", "msg"),
            "edit a message": ("edit", "change")
        }

        print("List of commands:")
        for desc, cmd in cmds.items():
            cmd = " | ".join(cmd)
            print(f"{cmd}{' ' * (32 - len(cmd))}{desc}")

    def create_message(self):
        """Create a new message"""

        uid = 0
        for item in self.the_list:
            if item[2] == self.username:
                uid += 1
        uid = f"{uid + 1}_{self.username}"

        msg = None
        while msg is None:
            userin = input("Enter a message: ")
            if self.is_msg_allowed(userin):
                msg = userin

        self.the_list.append((uid, msg, self.username, datetime.now().timestamp()))

    def edit_message(self):
        """Edit the text of a message"""

        msgid = None
        while msgid is None:
            userin = input("Enter the message number: ")
            if userin.isdecimal():
                userin = int(userin)
                if userin < len(self.the_list):
                    sel_msg = self.the_list[userin]
                    if sel_msg[2] == self.username:
                        confim = input(f"The currently selected message is \"{sel_msg[1]}\". Confirm (y/n)[y]: ")
                        if confim == "y" or confim == "yes" or confim == "":
                            msgid = userin
                    else:
                        print("You didn't send this message!")
                else:
                    print("A message with this id doesn't exist!")

        msg = None
        while msg is None:
            userin = input("Enter a message: ")
            if self.is_msg_allowed(userin):
                msg = userin

        self.the_list[msgid] = (sel_msg[0], msg, sel_msg[2], datetime.now().timestamp())

    def is_msg_allowed(self, msg: str) -> bool:
        invalid_chars = ["'", '"', ",", "(", ")"]
        for char in invalid_chars:
            if char in msg:
                return False
        
        return True

    def get_database(self) -> list[tuple[str, str]]:
        """Get the database"""

        sock = create_connection(self._conn_tuple)
        self._send(sock, "GET db")

        new_list = str_to_list(self._recv(sock))

        self.the_list = unify_lists(self.the_list, new_list)

    def keepalive_func(self):
        """Send a keepalive every 10 seconds"""

        while True:
            try:
                sock = create_connection(self._conn_tuple)
                self._send(sock, f"PING")
                assert self._recv(sock) == "ACK"
            except (ConnectionRefusedError, TimeoutError):
                print("Sending keepalive to server failed, retrying in 10s...")
            except (AssertionError) as aerr:
                print(aerr)

            sleep(10)

    def autosync_func(self):
        """Synchronize the database every 10 seconds"""

        while True:
            try:
                self.get_database()
                self.send_database()
            except (ConnectionRefusedError, TimeoutError):
                print("Autosync of database failed, retrying in 10s...")
            except (AssertionError) as aerr:
                print(aerr)

            sleep(10)

    def send_database(self):
        """Send the local database"""

        sock = create_connection(self._conn_tuple)
        self._send(sock, f"PUT db {self.the_list}")

        return self._recv(sock) == "ACK"

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
