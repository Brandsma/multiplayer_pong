import threading
import json
import time 
from network_interface import Network
from betterpong import Pong, GameState

ARTIFICIAL_PING = 0.200 #seconds

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

        # Send time to server
        t0 = time.time()
        t0_json = json.dumps(t0).encode("utf-8")
        t0_json += b"||"
        self.network.connection.send(t0_json)

        # Get time from server
        data = self.network.connection.recv(4096)    
        print(f"time: {data=}")
        times_received = data.split(b"||")
        t1 = json.loads(times_received[0])
        t2 = json.loads(times_received[1])
        print(f"{t1=}")
        print(f"{t2=}")
        t3 = time.time()

        print(f"{type(t1) = } {type(t2) = } {type(t3) = } {type(t0) = }")
        delta_time = ((t1 - t0) + (t2 - t3))/2
        print(f"{delta_time=}")

        while True:
            data = self.network.connection.recv(4096)    
            time.sleep(ARTIFICIAL_PING)
            now = time.time()        
            if not data:
                continue

            json_states = data.decode("utf-8").split("||")
            #print(f"json state: {json_states} type: {type(json_states)}")
            # if type(json_states) == str:
            #     now = time.time()
            #     print("received ping")
            #     ping = now - float(json_states.removeprefix('TIME:'))
            #     self.game.set_ping(ping)
            #     continue
            game_states = []
            for json_state in json_states:
                if json_state == "":
                    continue
                game_states.append(GameState.from_json(json_state))

            # print(f"CLIENT: game state= {game_state}")
            for game_state in game_states:
                if game_state == None:
                    continue

                self.game.set_gamestate(game_state)

                # Set ping                
                self.game.set_ping(now - game_state.cur_time + delta_time)

## Clock asynch time = (current_time - received_time) - travel time
## travel_time = time delta a->b + time delta b->a / 2


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
        json_event += b"||"
        self.network.connection.send(json_event)

    def connect(self):
        pass

    def disconnect(self):
        self.network.disconnect_client(self.player_id)

if __name__=="__main__":
    abe_local = "192.168.178.87"
    abe_public = "84.25.27.86"
    ivos_ip = "82.73.173.174"
    local = "localhost"
    abe_local = "192.168.178.87"


    client = Client(abe_public, 25565)
    client.keep_alive()