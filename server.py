import socket
from dataclasses import dataclass
from uuid import uuid4
import sys
import threading
from betterpong import Pong
import time

from network_data import NetworkData, TimeUpdate, PlayerInfo, PlayerInputEvent
from network_interface import NetworkGroup


class AuthoritativeServer:
    def __init__(self, server_ip, port):
        self.network_group = NetworkGroup(server_ip, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.bind_server(server_ip, port)

        # TODO self.game becomes self.room, and a game in there. A room will also have a network group
        self.game = Pong(name="Server Pong", run_with_viewer=False)
        self.game_thread = threading.Thread(target=self.game.server_run, args=(self,))

        self.game_thread.start()

    def quit_server(self):
        self.game_thread.join()

    def bind_server(self, ip, port):
        try:
            self.server_socket.bind((ip, port))
        except Exception as e:
            print(f"Failed to bind server: {e}")
        print("Server has been bounded")
        self.server_socket.listen()

    def listen_for_connections(self):
        print("Listening for connections...")
        # A thread is spawned per player
        while True:
            conn, (ip, port) = self.server_socket.accept()
            # Generate random player id
            player_id = str(uuid4())
            self.network_group.add_network(conn, ip, port, player_id)

            t = threading.Thread(target=self.client_thread, args=(conn, player_id))
            t.daemon = True
            t.start()

    def init_client(self, player_id):
        self.game.player_sequence_numbers[player_id] = 0

    def client_thread(self, connection, player_id):
        print(f"Started a thread for client {player_id}")

        self.init_client(player_id)
        # Send the player id to the client
        self.network_group.send_to_player(player_id, PlayerInfo(player_id))

        # Get time from client
        _ = self.network_group.receive_from_player(player_id, TimeUpdate, blocking=True)

        t1 = time.time()

        self.network_group.send_to_player(player_id, TimeUpdate(t1))

        while True:
            try:
                player_inputs = self.network_group.receive_from_player(
                    player_id, PlayerInputEvent, blocking=False
                )
                for player_input in player_inputs:
                    self.game.add_player_input_to_events(player_input)

            except ConnectionResetError as e:
                print(f"Remote host lost connection")
                self.network_group.remove_network_by_player_id(player_id)
                break
            except Exception as e:
                print(f"Client thread encountered exception: {e}\n")
                break

    def update_gamestate_for_all_connections(self):
        game_state = self.game.get_gamestate()
        game_state.cur_time = time.time()

        # print("Sending packet of size", sys.getsizeof(game_state.to_packet()), "bytes to client")

        for player_id in self.network_group.network_group:
            game_state.sequence_number = self.game.player_sequence_numbers[player_id]
            self.network_group.send_to_player(player_id, game_state)


if __name__ == "__main__":
    abes_ip = "84.25.27.86"
    laptop_abe_local_ip = "192.168.1.104"
    ivos_ip = "82.73.173.174"
    ivo_local = "192.168.178.102"
    abe_local = "192.168.178.87"
    abe_local_linux = "192.168.178.199"
    local_ip = "localhost"
    ip_uni = "145.97.151.17"

    server = AuthoritativeServer(abe_local_linux, 25565)
    server.listen_for_connections()
