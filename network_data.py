from dataclasses import asdict, dataclass
import json
import dacite


class NetworkData:
    incomplete_message = None

    def to_json(self):
        """Return JSON object of this data object, used when sending data."""
        jsonified_send_object = asdict(self)
        jsonified_send_object["class_type"] = type(self).__name__
        # print(jsonified_send_object["class_type"])
        return json.dumps(jsonified_send_object)

    @classmethod
    def from_json(cls, json_string, type_def=None):
        """Return data object of input JSON object, used when receiving data."""
        # print(f"from_json: {json_string=}")
        data = json.loads(json_string)
        if type_def is None:
            type_def = cls.deduce_class_type(data["class_type"])

        # TODO: Find a better place to instantiate these typehooks
        # Custom types (such as int enums) don't automatically convert, this needs an explicit mention as a 'type_hook'
        # The type hooks can be set here, where they are used. Or put in a location where it would be easier to add new special types.
        # type_hooks = {Controls: Controls}
        result = dacite.from_dict(
            data_class=type_def,
            data=data,  # config=dacite.Config(type_hooks=type_hooks)
        )
        return result

    def to_packet(self):
        """Encode data object to packet to send, first packing to JSON, then to binary"""
        return str.encode(self.to_json(), encoding="utf8") + b"||"

    @classmethod
    def _from_packet(cls, packet, type_def=None):
        """Decode data object from received packet, first decoding from binary, then to data object from JSON"""
        # print(packet.decode())
        return cls.from_json(packet.decode(), type_def=type_def)

    @classmethod
    def from_packets(cls, packets, type_def=None):
        """Decode data object from received packets, first decoding from binary, then to data object from JSON"""
        if packets == None:
            return []
        packets = packets.split(b"||")
        packets = [packet for packet in packets if packet != b""]
        return [cls._from_packet(packet, type_def=type_def) for packet in packets]

    @classmethod
    def deduce_class_type(cls, type_name):
        """When recieving a bytes object and translating it back to NetworkData object,
        we need to know what subtype of NetworkData we need to translate it to."""
        assert type(cls) == type(
            NetworkData
        ), "deduce_class_type should only be called on NetworkData class"

        return [
            subclass
            for subclass in cls.__subclasses__()  # look through all subclasses...
            if subclass.__name__ == type_name  # ...and select by type name
        ][0]


@dataclass
class TimeUpdate(NetworkData):
    time: float


@dataclass
class GameStateUpdate(NetworkData):
    game_state: dict
    game_tick: int
    request_id: int


@dataclass
class GameState(NetworkData):
    ball_pos: list
    ball_vel: list
    paddle1_pos: list
    paddle2_pos: list
    paddle1_vel: float
    paddle2_vel: float
    l_score: int
    r_score: int
    cur_time: float
    sequence_number: int


@dataclass
class PlayerInfo(NetworkData):
    player_id: str


@dataclass
class PlayerInputEvent(NetworkData):
    player_id: str
    key_value: int
    key_direction: int
    sequence_number: int
