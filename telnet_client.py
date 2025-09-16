import telnetlib, time, threading, re, traceback
from db import get_conn
from commands import CommandHandler

class TelnetBot:
    def __init__(self, host, port, password, server_id):
        self.host = host
        self.port = port
        self.password = password
        self.server_id = server_id
        self.conn = get_conn()
        self.online = {}  # eid -> {name, pos, steam, eos}
        self.tn = None
        self.running = False
        self.buf = b""
        self.commands = CommandHandler(self)

    def connect(self):
        while True:
            try:
                print(f"[econ] Connecting to {self.host}:{self.port}")
                self.tn = telnetlib.Telnet(self.host, self.port)
                time.sleep(0.2)
                self.tn.write((self.password + "\n").encode("utf-8"))
                time.sleep(0.5)
                self.tn.write(b"help\n")
                self.running = True
                threading.Thread(target=self._reader, daemon=True).start()
                break
            except Exception as e:
                print(f"[econ] Connection failed: {e}")
                time.sleep(5)

    def _reader(self):
        while self.running:
            try:
                chunk = self.tn.read_eager()
                if chunk:
                    self.buf += chunk
                    while b"\n" in self.buf:
                        line, self.buf = self.buf.split(b"\n", 1)
                        txt = line.decode("utf-8", errors="ignore").strip()
                        if txt:
                            print(f"[RAW] {txt}")
                            self._safe_dispatch(txt)
                else:
                    time.sleep(0.05)
            except Exception:
                print(traceback.format_exc())
                time.sleep(0.1)

    def _safe_dispatch(self, line):
        try:
            # --- Player position update from listplayers output ---
            m = re.search(r"id=(\d+).*name=([^,]+).*pos=\(([-\d]+), ([-\d]+), ([-\d]+)\)", line)
            if m:
                eid = int(m[1])
                name = m[2].strip()
                x, y, z = int(m[3]), int(m[4]), int(m[5])
                self.online[eid] = self.online.get(eid, {})
                self.online[eid].update({
                    "name": name,
                    "pos": (x, y, z),
                })

            self.commands.dispatch(line)
        except Exception:
            print(traceback.format_exc())

    def send(self, cmd: str):
        try:
            self.tn.write((cmd + "\n").encode("utf-8"))
            time.sleep(0.05)
            self.tn.write(b"rdd\n")
        except Exception as e:
            print(f"[econ] send error: {e}")

    def pm(self, eid: int, msg: str):
        self.send(f'pm {eid} "{msg}"')
