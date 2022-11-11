import socket

class Network:
    def __init__(self, server_ip="localhost", port=25565):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.port = port
        self.addr = (self.server_ip, self.port) 

        self.player_id = self.connect_player()
        
    def connect_player(self):
        try:
            self.connection.connect(self.addr)
            player_data = self.connection.recv(2048).decode("utf-8")
            return player_data
        except Exception as e:
            print(f"connect player error: {e}")
