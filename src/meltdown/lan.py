"""Zero-dependency local network (LAN) socket helper for MELTDOWN Versus."""

import hashlib
import json
import socket


def room_code_to_port(room_code: str) -> int:
    """Deterministically map a short room code (e.g. 'ABC123') to a high TCP port."""
    digest = hashlib.md5(room_code.strip().upper().encode("utf-8")).hexdigest()
    return 50000 + (int(digest[:4], 16) % 10000)


def get_local_ip() -> str:
    """Return best-effort local LAN IP address for display."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def send_json(sock: socket.socket, payload: dict) -> None:
    data = (json.dumps(payload) + "\n").encode("utf-8")
    sock.sendall(data)


def recv_json(sock: socket.socket, timeout: float = 60.0) -> dict:
    sock.settimeout(timeout)
    buf = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Peer disconnected")
        buf.extend(chunk)
        if b"\n" in buf:
            line = buf.split(b"\n", 1)[0]
            return json.loads(line.decode("utf-8"))


def host_lan_handshake(port: int, seed: int, diff: str, timeout: float = 45.0):
    """Wait for a LAN peer to connect, send seed+diff, and return connected socket."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.settimeout(timeout)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    try:
        conn, _ = srv.accept()
    finally:
        srv.close()
    send_json(conn, {"seed": seed, "diff": diff})
    return conn


def join_lan_handshake(host: str, port: int, timeout: float = 15.0):
    """Connect to a LAN host and receive (conn, seed, diff)."""
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.settimeout(timeout)
    conn.connect((host, port))
    info = recv_json(conn, timeout=timeout)
    return conn, int(info["seed"]), str(info["diff"])
