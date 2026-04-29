import json
import threading
import socket
from pathlib import Path


class WebsocketClient:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._running = False
        self._soc : socket.socket
        self.id = -1
        self.name = ""

    def connect(self):
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self._soc.connect((self._host, self._port))

    def login(self, username, password):
        soc = self._soc
        name_size_bytes = len(username).to_bytes(8, byteorder='big')
        password_size_bytes = len(password).to_bytes(8, byteorder='big')
        soc.sendall(
            name_size_bytes + 
            username.encode("utf-8") +
            password_size_bytes + 
            password.encode("utf-8")
        )
        team_exits : bytes | None = receive_data(soc, 1)
        if team_exits != b"T": return
        id_team_bytes : bytes | None = receive_data(soc, 1)
        id : int = int.from_bytes(id_team_bytes, 'big') if id_team_bytes is not None else -1

        return id

    def start_reading(self):
        self._running = True
        threading.Thread(
            target= self._read_loop,
            args=(),
            daemon=True
        ).start()

    def _read_loop(self):
        soc = self._soc
        while self._running:
            try:
                msg_type : bytes | None = receive_data(soc, 1)
                if msg_type is None:break
                msg_sender : bytes | None = receive_data(soc, 1)
                if msg_sender is None: break
                msg_sender_id : int = int.from_bytes(msg_sender, "big")
                msg_size : bytes | None= receive_data(soc, 8)
                if msg_size is None:break
                size = int.from_bytes(msg_size, "big")
                msg_content : bytes | None = receive_data(soc, size)
                if (msg_content is None):break
                sender_name = self.get_team_name_by_id(msg_sender_id)
                if sender_name is None : break

                self.save_msg(msg_type, sender_name, msg_sender_id, self.name, self.id, msg_content)
            except:
                ...

    def save_msg(self, msg_type : bytes, msg_sender : str, msg_sender_id : int, receiver_name : str, receiver_id : int, msg_content : bytes):
        if (msg_type == b"T"):
            msg = msg_content.decode("utf-8")
            print('\n'+msg+'\n')
            data = {
                "sender_id": msg_sender_id,
                "sender_name": msg_sender,
                "receiver_id": receiver_id,
                "receiver_name": receiver_name,
                "msg_type": "text",
                "content":msg
            }
            path = Path(f"chats/{self.id}_{self.name}_{msg_sender_id}_{msg_sender}.json")
            path.write_text(json.dumps(data)+",\n")
            return
        extension = ""

        match msg_type:
            case b"I": extension = ".jpg"
            case b"P": extension = ".pdf"

        path_images = Path("images")
        file_number = len(list(path_images.glob(extension)))
        file_name = f"images/chat_file_{file_number+1}{extension}"
        file = Path(file_name)
        file.write_bytes(msg_content)

        data = {
            "sender_id": msg_sender_id,
            "sender_name": msg_sender,
            "receiver_id": receiver_id,
            "receiver_name": receiver_name,
            "msg_type": extension,
            "content":file_name
        }

        Path(f"chats/{self.id}_{msg_sender_id}.json").write_text(json.dumps(data) + ",\n")

    def send_msg(self, msg_type : str, msg_receiver_id : int, msg_content):
        soc = self._soc
        data : bytes = \
        (
         msg_type.encode("utf-8") +
         msg_receiver_id.to_bytes(1, "big") +
         len(msg_content.encode("utf-8")).to_bytes(8, "big") + 
         msg_content.encode("utf-8")
        )
        soc.sendall(data)
        receiver_name : str | None= self.get_team_name_by_id(msg_receiver_id)
        if receiver_name is None: return
        self.save_msg(msg_type.encode("utf-8"), self.name, self.id, receiver_name, msg_receiver_id, msg_content)

    def get_team_name_by_id(self, id: int) -> str | None:
        self._running = False
        soc = self._soc
        soc.sendall(b"G" + id.to_bytes(1, "big"))
        team_name_syze : bytes | None = receive_data(soc, 1)
        if team_name_syze is None: 
            self._running = True
            return
        team_name : bytes | None = receive_data(soc, int.from_bytes(team_name_syze, "big"))
        if team_name is None: 
            self._running = True
            return
        self._running = True
        return team_name.decode("utf-8")

    def disconnect(self):
        # self._running == False             que??
        self._running = False
        try:
            self._soc.close()
        except Exception:
            pass

class AuthError(Exception):
    pass

def receive_data(soc, size):
    data = b""
    while len(data) < size:
        pack = soc.recv(size-len(data))
        if (not pack):
            return None
        data += pack
    return data
