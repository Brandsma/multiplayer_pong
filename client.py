import threading
import json
import time 
from network_interface import Network
from betterpong import Pong, GameState


class Client:

    def __init__(self, server, port):
        self.game = Pong(name="Client Pong")
        
        self.network = Network(server, port)

        t = threading.Thread(target=self.listen, args=())
        t.daemon = True
        t.start()

        self.game.client_run(self)


    def listen(self):
        print("Listening from client...")
        while True:
            data = self.network.connection.recv(4096)            
            if not data:
                continue

            game_state = GameState.from_json(data.decode("utf-8"))

            # print(f"CLIENT: game state= {game_state}")
            if game_state != None:
                self.game.set_gamestate(game_state)

    def keep_alive(self):
        print("keeping alive...")
        while True:
            try:
                time.sleep(5)
                continue
            except KeyboardInterrupt:
                print("Exiting from client.")
                exit()

    def send_event(self, event):
        json_event = json.dumps(event).encode("utf-8")
        self.network.connection.send(json_event)

    def connect(self):
        pass

    def disconnect(self):
        self.network.disconnect_client(self.player_id)

if __name__=="__main__":
    abe_local = "192.168.178.87"

    client = Client(abe_local, 25565)
    client.keep_alive()