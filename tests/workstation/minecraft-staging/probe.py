"""Bounded functional probes for the disposable staging server, never production."""

import argparse
import hashlib
import io
import json
import select
import socket
import struct
import time
import uuid
import zlib
from pathlib import Path

from minecraft_tools import msmp
from websockets.sync.client import connect

# Verified from the pinned 26.3 server's LoginProtocols, ConfigurationProtocols,
# GameProtocols and packet codecs (bundled server SHA256
# a362163eec5d1612d520772bc16e5b39c09e3b234fdc045f56bf544284ee8ae6).
# A version with a different wire protocol needs an explicit probe update.
PROTOCOL = 777
MAX_PACKET = 8 * 1024 * 1024


def varint(value):
    value &= 0xFFFFFFFF
    result = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        result.append(byte | (128 if value else 0))
        if not value:
            return bytes(result)


def read_varint(stream):
    result = 0
    for index in range(5):
        byte = stream.read(1)
        if len(byte) != 1:
            raise RuntimeError("unexpected end of protocol stream")
        result |= (byte[0] & 127) << (index * 7)
        if byte[0] < 128:
            return result
    raise RuntimeError("overlong protocol integer")


def string(value):
    encoded = value.encode()
    return varint(len(encoded)) + encoded


class Connection:
    def __init__(self, host, port):
        self.deadline = time.monotonic() + 120
        self.socket = socket.create_connection((host, port), timeout=10)
        self.compression = None

    def read(self, length):
        result = bytearray()
        while len(result) < length:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("staging connection deadline exceeded")
            self.socket.settimeout(min(remaining, 10))
            try:
                part = self.socket.recv(length - len(result))
            except socket.timeout:
                continue
            if not part:
                raise RuntimeError("server disconnected before probe completed")
            result.extend(part)
        return bytes(result)

    def send(self, packet_id, payload=b""):
        data = varint(packet_id) + payload
        if self.compression is not None:
            data = (
                varint(len(data)) + zlib.compress(data)
                if len(data) >= self.compression
                else b"\0" + data
            )
        self.socket.sendall(varint(len(data)) + data)

    def packet(self, wait_until=None):
        if wait_until is not None:
            remaining = min(wait_until, self.deadline) - time.monotonic()
            if remaining <= 0 or not select.select([self.socket], [], [], remaining)[0]:
                return None
        size = read_varint(self)
        if not 0 < size <= MAX_PACKET:
            raise RuntimeError("invalid staging packet size")
        data = self.read(size)
        if self.compression is not None:
            stream = io.BytesIO(data)
            uncompressed = read_varint(stream)
            if uncompressed:
                if uncompressed > MAX_PACKET:
                    raise RuntimeError("oversized compressed staging packet")
                decoder = zlib.decompressobj()
                data = decoder.decompress(stream.read(), MAX_PACKET + 1)
                if len(data) != uncompressed or not decoder.eof or decoder.unused_data:
                    raise RuntimeError("invalid compressed staging packet")
            else:
                data = stream.read()
        stream = io.BytesIO(data)
        return read_varint(stream), stream.read()

    def handshake(self, host, port, state, protocol):
        self.send(
            0, varint(protocol) + string(host) + struct.pack(">H", port) + varint(state)
        )

    def close(self):
        self.socket.close()


def game_probe(args):
    status = Connection(args.host, args.port)
    try:
        status.handshake(args.host, args.port, 1, -1)
        status.send(0)
        packet_id, payload = status.packet()
        if packet_id != 0:
            raise RuntimeError("invalid status response")
        stream = io.BytesIO(payload)
        advertised = json.loads(stream.read(read_varint(stream)))
        if advertised["version"]["name"] != args.expected_version:
            raise RuntimeError(
                "staging server game version does not match selected package"
            )
        if advertised["version"]["protocol"] != PROTOCOL:
            raise RuntimeError(
                "unsupported wire protocol; update the probe before qualifying this candidate"
            )
    finally:
        status.close()

    connection = Connection(args.host, args.port)
    player_id = uuid.UUID(
        bytes=hashlib.md5(("OfflinePlayer:" + args.player).encode()).digest(), version=3
    )
    try:
        connection.handshake(args.host, args.port, 2, PROTOCOL)
        connection.send(0, string(args.player) + player_id.bytes)
        state = "login"
        joined_at = None
        position = [0.0] * 5
        while joined_at is None or (
            time.monotonic() - joined_at < args.hold_seconds
            and (args.release_file is None or not args.release_file.exists())
        ):
            packet = connection.packet(
                wait_until=min(joined_at + args.hold_seconds, time.monotonic() + 0.5)
                if joined_at is not None
                else None
            )
            if packet is None:
                if time.monotonic() >= connection.deadline:
                    raise TimeoutError("staging connection deadline exceeded")
                continue
            packet_id, payload = packet
            if state == "login":
                if packet_id == 3:
                    connection.compression = read_varint(io.BytesIO(payload))
                elif packet_id == 2:
                    player_id = uuid.UUID(bytes=payload[:16])
                    connection.send(3)
                    state = "configuration"
                    # ClientInformation: locale, distance, chat, colors, skin,
                    # main hand, filtering, listing and particle status.
                    connection.send(
                        0, string("en_us") + b"\x02\x00\x01\x7f\x01\x00\x01\x00"
                    )
                elif packet_id == 4:
                    request = read_varint(io.BytesIO(payload))
                    connection.send(2, varint(request) + b"\0")
                else:
                    raise RuntimeError(f"unexpected login packet {packet_id}")
            elif state == "configuration":
                if packet_id == 2:
                    raise RuntimeError("server rejected staging configuration")
                if packet_id == 3:
                    connection.send(3)
                    state = "play"
                elif packet_id == 15:
                    connection.send(7, varint(0))  # Request full registry data.
                elif packet_id in (4, 5):
                    connection.send(packet_id, payload)
                elif packet_id == 20:
                    connection.send(
                        9
                    )  # Accept the disposable server's code of conduct.
                elif packet_id in (0, 9, 12):
                    raise RuntimeError(
                        "unsupported cookie, resource-pack or transfer request"
                    )
            else:
                if packet_id == 32:
                    raise RuntimeError("server disconnected the staging player")
                if packet_id == 45:
                    connection.send(28, payload)
                elif packet_id == 11:
                    connection.send(11, struct.pack(">f", 20.0))
                elif packet_id == 73:
                    packet = io.BytesIO(payload)
                    teleport_id = read_varint(packet)
                    x, y, z, _dx, _dy, _dz, yaw, pitch, relatives = struct.unpack(
                        ">6d2fI", packet.read()
                    )
                    # 26.3 requires absolute position/rotation in the reply,
                    # including relative updates to the previous client pose.
                    for index, value in enumerate((x, y, z, yaw, pitch)):
                        position[index] = (
                            position[index] + value
                            if relatives & (1 << index)
                            else value
                        )
                    connection.send(
                        0, varint(teleport_id) + struct.pack(">dddff", *position)
                    )
                    if joined_at is None:
                        connection.send(44)
                        joined_at = time.monotonic()
                        args.ready_file.write_text(
                            json.dumps(
                                {
                                    "player": args.player,
                                    "uuid": str(player_id),
                                    "protocol": PROTOCOL,
                                    "position_acknowledged": True,
                                }
                            )
                        )
        print(
            json.dumps(
                {"login": "passed", "player": args.player, "uuid": str(player_id)}
            )
        )
    finally:
        connection.close()


def management_probe(args):
    secret = msmp.read_secret_from_environment_file(args.secret_file)
    if msmp.SECRET_RE.fullmatch(secret) is None:
        raise RuntimeError("invalid staging fixture credential")
    with connect(
        f"ws://127.0.0.1:{args.port}",
        additional_headers={"Authorization": f"Bearer {secret}"},
        proxy=None,
        open_timeout=10,
        close_timeout=5,
    ) as websocket:
        session = msmp.MsmpSession(websocket)
        session.require_backup_capabilities(
            timeout=20,
            additional_capabilities=("minecraft:players",)
            if args.expected_players
            else (),
        )
        result = session.call("minecraft:server/status", timeout=20)
        if result.get("started") is not True:
            raise RuntimeError("staging world is not initialized")

        def require_players():
            if args.expected_players:
                players = session.call("minecraft:players", timeout=20)
                if {player["name"] for player in players} != set(args.expected_players):
                    raise RuntimeError("expected simultaneous staging players missing")

        require_players()
        if args.save:
            session.save_and_wait(timeout=120)
        require_players()
    print(json.dumps({"initialized": True, "save": args.save}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    game = subparsers.add_parser("game")
    game.add_argument("--host", required=True)
    game.add_argument("--port", type=int, required=True)
    game.add_argument("--expected-version", required=True)
    game.add_argument("--player", default="StageProbe")
    game.add_argument("--ready-file", type=Path, required=True)
    game.add_argument("--release-file", type=Path)
    game.add_argument("--hold-seconds", type=float, default=20)
    management = subparsers.add_parser("management")
    management.add_argument("--port", type=int, required=True)
    management.add_argument("--secret-file", type=Path, required=True)
    management.add_argument("--save", action="store_true")
    management.add_argument("--expected-players", nargs="+")
    args = parser.parse_args()
    {"game": game_probe, "management": management_probe}[args.operation](args)


if __name__ == "__main__":
    main()
