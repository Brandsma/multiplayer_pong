import socket
from network_data import NetworkData, PlayerInfo
import time


class NetworkGroup:
    def __init__(self, server_ip="localhost", port=25565):
        self.server_ip = server_ip
        self.port = port
        self.addr = (self.server_ip, self.port)
        self.network_group = {}

    def add_network(self, connection, ip, port, player_id):
        self.network_group[player_id] = Network(
            socket=connection,
            server_ip=ip,
            port=port,
        )

    def remove_network_by_player_id(self, player_id):
        del self.network_group[player_id]

    def remove_network_by_connection(self, connection):
        for player_id, network in self.network_group.items():
            if network.connection == connection:
                del self.network_group[player_id]

    def send_to_all(self, data: NetworkData):
        for _, network in self.network_group.items():
            network.send(data)

    def send_to_player(self, player_id, network_data: NetworkData):
        self.network_group[player_id].send(network_data)

    def receive_from_player(
        self,
        player_id,
        expected_type: type = None,
        blocking: bool = False,
        timeout: float = 0.01,
        max_size: int = 4096,
        max_timeout: float = 1,
    ):
        return self.network_group[player_id].receive(
            expected_type, blocking, timeout, max_size, max_timeout
        )


class Network:
    def __init__(self, socket, server_ip="localhost", port=25565):
        self.connection = socket
        self.server_ip = server_ip
        self.port = port
        self.incomplete_message_buffer = None

        self.network_data_buffer = {}

    def connect_socket(self):
        try:
            self.connection.connect((self.server_ip, self.port))
        except Exception as e:
            print(f"Failed to connect to server: {e}")

    def receive(
        self,
        expected_type: type = None,
        blocking: bool = False,
        timeout: float = 0.01,
        max_size: int = 4096,
        max_timeout: float = 1,
    ):
        # TODO: Add max recursion depth exception handling

        # receive the data
        received_data = self.connection.recv(max_size)

        received_data = self.handle_incomplete_message(received_data)

        parsed_packages = NetworkData.from_packets(received_data)

        for parsed_package in parsed_packages:
            # parse the data
            if type(parsed_package) not in self.network_data_buffer:
                self.network_data_buffer[type(parsed_package)] = []
            self.network_data_buffer[type(parsed_package)].append(parsed_package)

        # If the data is the expected type or no expected type is given, return the data
        if expected_type == None:
            if len(parsed_packages) == 0:
                return None
            result = parsed_packages[0]
            self.network_data_buffer[type(result)].remove(result)
            return result

        # If the expected data type data is in the buffer, return it. This also clears the buffer if no packages are revceived
        if (
            expected_type in self.network_data_buffer
            and len(self.network_data_buffer[expected_type]) != 0
        ):
            return self.network_data_buffer[expected_type].pop(0)
        # If blocking, wait for the expected type
        elif blocking:
            time.sleep(timeout)
            if timeout < max_timeout:
                timeout *= 2
            if timeout > max_timeout:
                print("Max timeout reached")
                timeout = max_timeout
            return self.receive(expected_type, blocking, timeout, max_size)
        else:
            return None

    def send(self, data):
        self.connection.send(data.to_packet())

    def handle_incomplete_message(self, received_data):
        """Handles incomplete messages by appending the incomplete message to the next message"""
        if self.incomplete_message_buffer != None:
            received_data = self.incomplete_message_buffer + received_data
            self.incomplete_message_buffer = None

        if received_data != None and received_data[-2:] != b"||":
            split_idx = received_data.rfind(b"||")
            if split_idx != -1:
                self.incomplete_message_buffer = received_data
            else:
                self.incomplete_message_buffer = received_data[split_idx:]
                received_data = received_data[:split_idx]
        return received_data
