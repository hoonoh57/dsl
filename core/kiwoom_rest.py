"""Minimal Kiwoom REST market-data adapter (orders deliberately excluded)."""
from __future__ import annotations

import json
import os
import base64
import hashlib
import secrets
import socket
import ssl
import struct
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


class KiwoomAPIError(RuntimeError):
    pass


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path = ENV_PATH) -> bool:
    """Load a small dotenv file without adding a runtime dependency.

    Existing process variables win over file values. Comments, optional
    ``export`` prefixes, and single/double quoted values are supported.
    """
    if not path.is_file():
        return False
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key or not key.replace("_", "").isalnum():
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)
    return True


load_env()


@dataclass
class KiwoomConfig:
    app_key: str = ""
    secret_key: str = ""
    mock: bool = True

    @property
    def base_url(self):
        return "https://mockapi.kiwoom.com" if self.mock else "https://api.kiwoom.com"

    @classmethod
    def from_env(cls):
        load_env()
        return cls(os.getenv("KIWOOM_APP_KEY", ""), os.getenv("KIWOOM_SECRET_KEY", ""),
                   os.getenv("KIWOOM_ENV", "mock").lower() != "live")


TIMEFRAMES = {
    "tick": ("ka10079", {}), "1m": ("ka10080", {"tic_scope": "1"}),
    "3m": ("ka10080", {"tic_scope": "3"}), "5m": ("ka10080", {"tic_scope": "5"}),
    "10m": ("ka10080", {"tic_scope": "10"}), "15m": ("ka10080", {"tic_scope": "15"}),
    "30m": ("ka10080", {"tic_scope": "30"}), "60m": ("ka10080", {"tic_scope": "60"}),
    "1d": ("ka10081", {}), "1w": ("ka10082", {}), "1M": ("ka10083", {}),
}


class KiwoomRESTClient:
    def __init__(self, config: KiwoomConfig | None = None):
        self.config = config or KiwoomConfig.from_env()
        self.token = ""

    def _post(self, path: str, body: Dict, api_id: str | None = None):
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        if api_id:
            if not self.token: self.authenticate()
            headers.update({"authorization": f"Bearer {self.token}", "api-id": api_id})
        request = urllib.request.Request(self.config.base_url + path, json.dumps(body).encode(), headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8")), dict(response.headers)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise KiwoomAPIError(f"키움 API HTTP {exc.code}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise KiwoomAPIError(f"키움 API 연결 실패: {exc.reason}") from exc

    def authenticate(self):
        if not self.config.app_key or not self.config.secret_key:
            raise KiwoomAPIError("KIWOOM_APP_KEY와 KIWOOM_SECRET_KEY가 설정되지 않았습니다.")
        data, _ = self._post("/oauth2/token", {"grant_type": "client_credentials",
                                               "appkey": self.config.app_key, "secretkey": self.config.secret_key})
        self.token = data.get("token", "")
        if not self.token: raise KiwoomAPIError(f"접근 토큰이 응답에 없습니다: {data.get('return_msg', 'unknown')}")
        return data

    def chart(self, symbol: str, timeframe: str = "1d", end_date: str = "") -> Dict:
        if timeframe not in TIMEFRAMES: raise KiwoomAPIError(f"지원하지 않는 timeframe: {timeframe}")
        api_id, extra = TIMEFRAMES[timeframe]
        body = {"stk_cd": symbol, "upd_stkpc_tp": "1", **extra}
        if api_id in ("ka10081", "ka10082", "ka10083"):
            body["base_dt"] = end_date
        data, headers = self._post("/api/dostk/chart", body, api_id)
        return {"api_id": api_id, "data": data, "continuation": headers.get("cont-yn", "N"),
                "next_key": headers.get("next-key", "")}

    def test_websocket_login(self, timeout: float = 8.0) -> Dict:
        """Perform a real RFC6455 handshake and Kiwoom LOGIN, then disconnect."""
        if not self.token: self.authenticate()
        host = "mockapi.kiwoom.com" if self.config.mock else "api.kiwoom.com"
        raw = socket.create_connection((host, 10000), timeout=timeout)
        sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
        sock.settimeout(timeout)
        try:
            key = base64.b64encode(secrets.token_bytes(16)).decode()
            request = (f"GET /api/dostk/websocket HTTP/1.1\r\nHost: {host}:10000\r\n"
                       f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                       "Sec-WebSocket-Version: 13\r\n\r\n")
            sock.sendall(request.encode("ascii"))
            response = b""
            while b"\r\n\r\n" not in response:
                response += sock.recv(4096)
                if len(response) > 16384: raise KiwoomAPIError("WSS 핸드셰이크 응답이 너무 큽니다.")
            header, remainder = response.split(b"\r\n\r\n", 1)
            if b" 101 " not in header.split(b"\r\n", 1)[0]:
                raise KiwoomAPIError(f"WSS 핸드셰이크 실패: {header.splitlines()[0].decode(errors='replace')}")
            expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest())
            if expected.lower() not in header.lower(): raise KiwoomAPIError("WSS 서버 서명 검증 실패")
            self._ws_send_text(sock, json.dumps({"trnm": "LOGIN", "token": self.token}))
            message = self._ws_read_text(sock, remainder)
            payload = json.loads(message)
            if int(payload.get("return_code", -1)) != 0:
                raise KiwoomAPIError(f"WSS 로그인 실패: {payload.get('return_msg', 'unknown')}")
            return {"connected": True, "message": "LOGIN 성공"}
        finally:
            sock.close()

    @staticmethod
    def _ws_send_text(sock, text: str):
        payload = text.encode("utf-8"); mask = secrets.token_bytes(4); length = len(payload)
        header = bytearray([0x81])
        if length < 126: header.append(0x80 | length)
        elif length < 65536: header.extend([0x80 | 126]); header.extend(struct.pack("!H", length))
        else: header.extend([0x80 | 127]); header.extend(struct.pack("!Q", length))
        masked = bytes(value ^ mask[i % 4] for i, value in enumerate(payload))
        sock.sendall(bytes(header) + mask + masked)

    @staticmethod
    def _ws_read_text(sock, initial=b""):
        buffer = bytearray(initial)
        def take(count):
            while len(buffer) < count: buffer.extend(sock.recv(4096))
            value = bytes(buffer[:count]); del buffer[:count]; return value
        first, second = take(2); opcode, length = first & 0x0F, second & 0x7F
        if length == 126: length = struct.unpack("!H", take(2))[0]
        elif length == 127: length = struct.unpack("!Q", take(8))[0]
        mask = take(4) if second & 0x80 else None
        payload = take(length)
        if mask: payload = bytes(value ^ mask[i % 4] for i, value in enumerate(payload))
        if opcode not in (1, 2): raise KiwoomAPIError(f"예상하지 못한 WSS opcode: {opcode}")
        return payload.decode("utf-8")

    @staticmethod
    def normalize_chart(payload: Dict) -> Dict[str, List]:
        container = payload.get("data", payload)
        if int(container.get("return_code", 0)) != 0:
            raise KiwoomAPIError(f"키움 차트 조회 실패: {container.get('return_msg', 'unknown')}")
        chart_keys = ("stk_tick_pole_chart_qry", "stk_min_pole_chart_qry", "stk_dt_pole_chart_qry",
                      "stk_stk_pole_chart_qry", "stk_mth_pole_chart_qry")
        rows = next((container[key] for key in chart_keys if isinstance(container.get(key), list)), None)
        if rows is None:
            rows = next((value for value in container.values() if isinstance(value, list)), [])
        def pick(row, *names, default="0"):
            return next((row[name] for name in names if name in row), default)
        def number(value):
            text = str(value).replace(",", "").strip()
            return abs(float(text or 0))
        result = {key: [] for key in ("time", "open", "high", "low", "close", "volume")}
        seen = set()
        for row in reversed(rows):
            timestamp = str(pick(row, "cntr_tm", "dt", "date", "base_dt", default=""))
            if not timestamp or timestamp in seen:
                continue
            seen.add(timestamp)
            result["time"].append(timestamp)
            result["open"].append(number(pick(row, "open_pric", "open", "open_price")))
            result["high"].append(number(pick(row, "high_pric", "high", "high_price")))
            result["low"].append(number(pick(row, "low_pric", "low", "low_price")))
            result["close"].append(number(pick(row, "cur_prc", "close", "close_price")))
            result["volume"].append(number(pick(row, "trde_qty", "volume")))
        if not result["time"]:
            available = ", ".join(sorted(container.keys()))
            raise KiwoomAPIError(f"차트 응답에서 봉 데이터를 찾지 못했습니다. 응답 필드: {available}")
        return result
