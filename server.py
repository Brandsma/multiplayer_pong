import socket
import json
from dataclasses import dataclass
from uuid import uuid4
import threading
from betterpong import Pong


class Game:
    def __init__(self):
        pass

    def init_game(self):
        pass

    def run(self):
        pass

    def tick(self):
        # perform tick action
        pass


class AuthoritativeServer:

    def __init__(self, server_ip, port):
        self.ip: str = server_ip
        self.port: int = port
        self.connections: set = set()
        self.server = None

        self.bind_server((self.ip, self.port))

        self.game = Pong(name = "Server Pong")
        self.game_thread = threading.Thread(target= self.game.server_run, args=(self, ))
        
        
        self.game_thread.start()

    def quit_server(self):
        self.game_thread.join()

    def bind_server(self, addr):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind(addr)
        except Exception as e:
            raise Exception(f"Failed to bind server: {e}")
        print("Server has been bounded")
        self.server.listen()

    def listen_for_connections(self):
        print("Listening for connections...")
        # A thread is spawned per player
        while True:
            conn, addr = self.server.accept()
            # Generate random player id
            player_id = str(uuid4())
            self.connections.add((conn, addr, player_id))

            t = threading.Thread(target=self.client_thread, args=(conn, addr, player_id))
            t.daemon = True
            t.start()
            
    def client_thread(self, connection, address, player_id):
        print(f"Started a thread for client {player_id}")

        # Send the player id to the client
        connection.send(player_id.encode("utf-8"))

        while True:
            try:

                data = connection.recv(4096)
                # If nothing got sent, wait
                if not data:
                    continue
                # print(f" -- client thread {player_id}: {data=}")
                player_event = json.loads(data)#.decode("utf-8")
                self.game.add_player_input_to_events(player_event)

                
            except ConnectionResetError as e:
                print(f"Remote host lost connection")
                self.connections.remove((connection, address, player_id))
                #print(e)
                break
            except Exception as e:
                print(
                    f"Client thread encountered exception: {e}\n"
                )
                break

    def update_gamestate_for_all_connections(self):
        for connection, _, _ in self.connections:
            connection.send(self.game.get_gamestate().to_json().encode("utf-8"))



if __name__=="__main__":
    abes_ip = "217.105.109.132"
    laptop_abe_local_ip = "192.168.1.104"
    ivos_ip = "87.214.136.100"
    ivo_local = "192.168.1.124"
    abe_local = "192.168.178.87"
    local_ip = "localhost"
    ip_uni = "145.97.151.17"

    server = AuthoritativeServer(abe_local, 25565)
    server.listen_for_connections()
