import socket
import threading


class ClientConnection:
    def __init__(self, host, port):
        self.soc = self._connect(host, port)
        threading.Thread(
            target=self.recv_data,
            args=(),
            daemon=True
        )

        threading.Thread(
            target=self.recv_data,
            args=(),
            daemon=True
        )

    def _connect(self, host, port):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        soc.connect((host, port))
        return soc

    def recv_data(self):
        ...

    def send_data(self):
        ...


