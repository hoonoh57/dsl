"""Minimal Kiwoom REST market-data adapter (orders deliberately excluded)."""
from __future__ import annotations

import base64
import hashlib
import json
import os
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
    """Load a small dotenv file without adding a runtime dependency."""
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
        return cls(
            os.getenv("KIWOOM_APP_KEY", ""),
            os.getenv("KIWOOM_SECRET_KEY", ""),
            os.getenv("KIWOOM_ENV", "mock").lower() != "live",
        )


TIMEFRAMES = {
    "tick": ("ka10079", {}),
    "1m": ("ka10080", {"tic_scope": "1"}),
    "3m": ("ka10080", {"tic_scope": "3"}),
    "5m": ("ka10080", {"tic_scope": "5"}),
    "10m": ("ka10080", {"tic_scope": "10"}),
    "15m": ("ka10080", {"tic_scope": "15"}),
    "30m": ("ka10080", {"tic_scope": "30"}),
    "60m": ("ka10080", {"tic_scope": "60"}),
    "1d": ("ka10081", {}),
    "1w": ("ka10082", {}),
    "1M": ("ka10083", {}),
}


def _digits(value) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


class KiwoomRESTClient:
    def __init__(self, config: KiwoomConfig | None = None):
        self.config = config or KiwoomConfig.from_env()
        self.token = ""

    def _post(
        self,
        path: str,
        body: Dict,
        api_id: str | None = None,
        *,
        continuation: str = "",
        next_key: str = "",
    ):
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        if api_id:
            if not self.token:
                self.authenticate()
            headers.update({"authorization": f"Bearer {self.token}", "api-id": api_id})
        if continuation:
            headers["cont-yn"] = str(continuation)
        if next_key:
            headers["next-key"] = str(next_key)
        request = urllib.request.Request(
            self.config.base_url + path,
            json.dumps(body).encode(),
            headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_headers = {
                    str(key).lower(): value for key, value in response.headers.items()
                }
                return json.loads(response.read().decode("utf-8")), response_headers
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise KiwoomAPIError(f"키움 API HTTP {exc.code}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise KiwoomAPIError(f"키움 API 연결 실패: {exc.reason}") from exc

    def authenticate(self):
        if not self.config.app_key or not self.config.secret_key:
            raise KiwoomAPIError("KIWOOM_APP_KEY와 KIWOOM_SECRET_KEY가 설정되지 않았습니다.")
        data, _ = self._post(
            "/oauth2/token",
            {
                "grant_type": "client_credentials",
                "appkey": self.config.app_key,
                "secretkey": self.config.secret_key,
            },
        )
        self.token = data.get("token", "")
        if not self.token:
            raise KiwoomAPIError(
                f"접근 토큰이 응답에 없습니다: {data.get('return_msg', 'unknown')}"
            )
        return data

    @staticmethod
    def format_symbol(symbol: str, venue: str = "KRX") -> str:
        """Return an explicit Kiwoom exchange-qualified symbol.

        KRX keeps the bare code, NXT uses ``_NX`` and integrated SOR uses
        ``_AL``.  A conflicting already-qualified suffix fails closed.
        """
        value = str(symbol).strip().upper()
        if not value:
            raise KiwoomAPIError("종목코드가 비어 있습니다.")
        venue = str(venue).strip().upper()
        suffixes = {"KRX": "", "NXT": "_NX", "SOR": "_AL", "AL": "_AL"}
        if venue not in suffixes:
            raise KiwoomAPIError(f"지원하지 않는 venue: {venue}")
        existing = "_AL" if value.endswith("_AL") else ("_NX" if value.endswith("_NX") else "")
        wanted = suffixes[venue]
        if existing:
            if existing != wanted:
                raise KiwoomAPIError(
                    f"종목코드 suffix({existing})와 요청 venue({venue})가 충돌합니다."
                )
            return value
        return value + wanted

    def chart(
        self,
        symbol: str,
        timeframe: str = "1d",
        end_date: str = "",
        *,
        continuation: str = "",
        next_key: str = "",
    ) -> Dict:
        if timeframe not in TIMEFRAMES:
            raise KiwoomAPIError(f"지원하지 않는 timeframe: {timeframe}")
        api_id, extra = TIMEFRAMES[timeframe]
        body = {"stk_cd": symbol, "upd_stkpc_tp": "1", **extra}
        if api_id in ("ka10081", "ka10082", "ka10083"):
            body["base_dt"] = end_date
        data, headers = self._post(
            "/api/dostk/chart",
            body,
            api_id,
            continuation=continuation,
            next_key=next_key,
        )
        return {
            "api_id": api_id,
            "data": data,
            "continuation": str(headers.get("cont-yn", "N")).upper(),
            "next_key": str(headers.get("next-key", "")),
        }

    @staticmethod
    def merge_normalized(markets: List[Dict[str, List]]) -> Dict[str, List]:
        """Merge paginated normalized pages by exact timestamp."""
        rows = {}
        for market in markets:
            lengths = {key: len(market.get(key, [])) for key in ("time", "open", "high", "low", "close", "volume")}
            if len(set(lengths.values())) != 1:
                raise KiwoomAPIError(f"페이지 OHLCV 길이가 일치하지 않습니다: {lengths}")
            for i, timestamp in enumerate(market["time"]):
                key = str(timestamp)
                row = tuple(float(market[field][i]) for field in ("open", "high", "low", "close", "volume"))
                if key in rows and rows[key] != row:
                    raise KiwoomAPIError(f"연속조회 페이지에 충돌하는 중복 timestamp가 있습니다: {key}")
                rows[key] = row
        ordered = sorted(rows)
        result = {key: [] for key in ("time", "open", "high", "low", "close", "volume")}
        for timestamp in ordered:
            o, h, l, c, v = rows[timestamp]
            result["time"].append(timestamp)
            result["open"].append(o)
            result["high"].append(h)
            result["low"].append(l)
            result["close"].append(c)
            result["volume"].append(v)
        if not result["time"]:
            raise KiwoomAPIError("병합할 차트 봉이 없습니다.")
        return result

    def chart_history(
        self,
        symbol: str,
        timeframe: str,
        *,
        venue: str = "KRX",
        end_date: str = "",
        required_bars: int = 0,
        required_start: str = "",
        max_pages: int = 20,
    ) -> Dict:
        """Fetch enough continuation pages to satisfy an explicit coverage contract.

        The Kiwoom continuation headers are replayed exactly on the next request.
        The method fails closed when the requested bar count/start coverage cannot
        be proven within ``max_pages`` or before the server exhausts history.
        """
        if required_bars < 0:
            raise KiwoomAPIError("required_bars는 0 이상이어야 합니다.")
        if max_pages < 1:
            raise KiwoomAPIError("max_pages는 1 이상이어야 합니다.")
        if not required_bars and not required_start:
            raise KiwoomAPIError("chart_history에는 required_bars 또는 required_start가 필요합니다.")
        qualified = self.format_symbol(symbol, venue)
        pages = []
        continuation = ""
        next_key = ""
        exhausted = False
        merged = None

        for page_index in range(max_pages):
            raw = self.chart(
                qualified,
                timeframe,
                end_date,
                continuation=continuation,
                next_key=next_key,
            )
            pages.append(self.normalize_chart(raw))
            merged = self.merge_normalized(pages)
            enough_bars = not required_bars or len(merged["time"]) >= int(required_bars)
            enough_start = (
                not required_start
                or _digits(merged["time"][0]) <= _digits(required_start)
            )
            if enough_bars and enough_start:
                break
            continuation = str(raw.get("continuation", "N")).upper()
            next_key = str(raw.get("next_key", ""))
            if continuation != "Y":
                exhausted = True
                break
            if not next_key:
                raise KiwoomAPIError("연속조회 응답이 Y인데 next-key가 비어 있습니다.")
        else:
            page_index = max_pages - 1

        if merged is None:
            raise KiwoomAPIError("차트 조회 결과가 없습니다.")
        enough_bars = not required_bars or len(merged["time"]) >= int(required_bars)
        enough_start = not required_start or _digits(merged["time"][0]) <= _digits(required_start)
        if not enough_bars or not enough_start:
            reason = "서버 history exhausted" if exhausted else f"max_pages={max_pages} 도달"
            raise KiwoomAPIError(
                "요청한 warm-up/history coverage를 충족하지 못했습니다: "
                f"bars={len(merged['time'])}, start={merged['time'][0]}, "
                f"required_bars={required_bars}, required_start={required_start}, {reason}"
            )
        return {
            "symbol": qualified,
            "timeframe": timeframe,
            "market": merged,
            "coverage": {
                "pages": len(pages),
                "bars": len(merged["time"]),
                "actual_start": merged["time"][0],
                "actual_end": merged["time"][-1],
                "required_bars": int(required_bars),
                "required_start": str(required_start),
                "continuation_exhausted": exhausted,
            },
        }

    def test_websocket_login(self, timeout: float = 8.0) -> Dict:
        """Perform a real RFC6455 handshake and Kiwoom LOGIN, then disconnect."""
        if not self.token:
            self.authenticate()
        host = "mockapi.kiwoom.com" if self.config.mock else "api.kiwoom.com"
        raw = socket.create_connection((host, 10000), timeout=timeout)
        sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
        sock.settimeout(timeout)
        try:
            key = base64.b64encode(secrets.token_bytes(16)).decode()
            request = (
                f"GET /api/dostk/websocket HTTP/1.1\r\nHost: {host}:10000\r\n"
                f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            )
            sock.sendall(request.encode("ascii"))
            response = b""
            while b"\r\n\r\n" not in response:
                response += sock.recv(4096)
                if len(response) > 16384:
                    raise KiwoomAPIError("WSS 핸드셰이크 응답이 너무 큽니다.")
            header, remainder = response.split(b"\r\n\r\n", 1)
            if b" 101 " not in header.split(b"\r\n", 1)[0]:
                raise KiwoomAPIError(
                    f"WSS 핸드셰이크 실패: {header.splitlines()[0].decode(errors='replace')}"
                )
            expected = base64.b64encode(
                hashlib.sha1(
                    (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
                ).digest()
            )
            if expected.lower() not in header.lower():
                raise KiwoomAPIError("WSS 서버 서명 검증 실패")
            self._ws_send_text(
                sock, json.dumps({"trnm": "LOGIN", "token": self.token})
            )
            message = self._ws_read_text(sock, remainder)
            payload = json.loads(message)
            if int(payload.get("return_code", -1)) != 0:
                raise KiwoomAPIError(
                    f"WSS 로그인 실패: {payload.get('return_msg', 'unknown')}"
                )
            return {"connected": True, "message": "LOGIN 성공"}
        finally:
            sock.close()

    @staticmethod
    def _ws_send_text(sock, text: str):
        payload = text.encode("utf-8")
        mask = secrets.token_bytes(4)
        length = len(payload)
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.extend([0x80 | 126])
            header.extend(struct.pack("!H", length))
        else:
            header.extend([0x80 | 127])
            header.extend(struct.pack("!Q", length))
        masked = bytes(value ^ mask[i % 4] for i, value in enumerate(payload))
        sock.sendall(bytes(header) + mask + masked)

    @staticmethod
    def _ws_read_text(sock, initial=b""):
        buffer = bytearray(initial)

        def take(count):
            while len(buffer) < count:
                buffer.extend(sock.recv(4096))
            value = bytes(buffer[:count])
            del buffer[:count]
            return value

        first, second = take(2)
        opcode, length = first & 0x0F, second & 0x7F
        if length == 126:
            length = struct.unpack("!H", take(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", take(8))[0]
        mask = take(4) if second & 0x80 else None
        payload = take(length)
        if mask:
            payload = bytes(value ^ mask[i % 4] for i, value in enumerate(payload))
        if opcode not in (1, 2):
            raise KiwoomAPIError(f"예상하지 못한 WSS opcode: {opcode}")
        return payload.decode("utf-8")

    @staticmethod
    def normalize_chart(payload: Dict) -> Dict[str, List]:
        container = payload.get("data", payload)
        if int(container.get("return_code", 0)) != 0:
            raise KiwoomAPIError(
                f"키움 차트 조회 실패: {container.get('return_msg', 'unknown')}"
            )
        chart_keys = (
            "stk_tick_pole_chart_qry",
            "stk_min_pole_chart_qry",
            "stk_dt_pole_chart_qry",
            "stk_stk_pole_chart_qry",
            "stk_mth_pole_chart_qry",
        )
        rows = next(
            (container[key] for key in chart_keys if isinstance(container.get(key), list)),
            None,
        )
        if rows is None:
            rows = next(
                (value for value in container.values() if isinstance(value, list)),
                [],
            )

        def pick(row, *names, default="0"):
            return next((row[name] for name in names if name in row), default)

        def number(value):
            text = str(value).replace(",", "").strip()
            return abs(float(text or 0))

        result = {
            key: [] for key in ("time", "open", "high", "low", "close", "volume")
        }
        seen = set()
        for row in reversed(rows):
            timestamp = str(
                pick(row, "cntr_tm", "dt", "date", "base_dt", default="")
            )
            if not timestamp or timestamp in seen:
                continue
            seen.add(timestamp)
            result["time"].append(timestamp)
            result["open"].append(
                number(pick(row, "open_pric", "open", "open_price"))
            )
            result["high"].append(
                number(pick(row, "high_pric", "high", "high_price"))
            )
            result["low"].append(
                number(pick(row, "low_pric", "low", "low_price"))
            )
            result["close"].append(
                number(pick(row, "cur_prc", "close", "close_price"))
            )
            result["volume"].append(number(pick(row, "trde_qty", "volume")))
        if not result["time"]:
            available = ", ".join(sorted(container.keys()))
            raise KiwoomAPIError(
                f"차트 응답에서 봉 데이터를 찾지 못했습니다. 응답 필드: {available}"
            )
        return result
