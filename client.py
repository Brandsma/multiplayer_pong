import threading
import time
from network_data import NetworkData, TimeUpdate, GameStateUpdate, GameState, PlayerInfo
from network_interface import Network
from betterpong import Pong
import socket

ARTIFICIAL_PING = 0.0000  # seconds


class Client:
    def __init__(self, server, port):
        self.game = Pong(name="Client Pong")

        self.network = Network(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM), server, port
        )
        self.network.connect_socket()
        self.connection_info = self.get_connection_info()

        t = threading.Thread(target=self.listen, args=())
        t.daemon = True
        t.start()

        self.game.client_run(self)

    def listen(self):
        print("Listening from client...")

        delta_time = self.get_server_time_delta()

        while True:

            game_states = self.network.receive(GameState, blocking=False)
            time.sleep(ARTIFICIAL_PING)
            now = time.time()

            for game_state in game_states:
                self.game.set_gamestate(game_state)
                # Set ping
                self.game.set_ping(now - game_state.cur_time + delta_time)

    def get_server_time_delta(self):
        ## Clock asynch time = (current_time - received_time) - travel time
        ## travel_time = time delta a->b + time delta b->a / 2
        # Send time to server
        t0 = time.time()
        self.network.send(TimeUpdate(t0))
        # Get time from server
        t1 = self.network.receive(TimeUpdate, blocking=True, max_return_count=1)[0]
        t2 = time.time()
        delta_time = ((t1.time - t0) + (t1.time - t2)) / 2

        return delta_time

    def keep_alive(self):
        print("keeping alive...")
        while True:
            try:
                time.sleep(5)
                continue
            except KeyboardInterrupt:
                print("Exiting from client.")
                exit()

    def send(self, data: NetworkData):
        self.network.send(data)

    def get_connection_info(self):
        connection_info = {}
        connection_info["player_data"] = self.network.receive(
            expected_type=PlayerInfo, blocking=True, max_return_count=1
        )[0]
        # NOTE Add more connection info here
        print(
            f"Connected to server with player id: {connection_info['player_data'].player_id}"
        )
        return connection_info

    def disconnect(self):
        self.network.disconnect_client(self.player_id)


if __name__ == "__main__":
    abe_local = "192.168.178.87"
    abe_local_linux = "192.168.178.199"
    abe_public = "84.25.27.86"
    ivos_ip = "82.73.173.174"
    ivos_local = "192.168.178.102"
    local = "localhost"
    abe_local = "192.168.178.87"

    client = Client(abe_local_linux, 25565)
    client.keep_alive()
