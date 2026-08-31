"""Non-repainting higher-timeframe aggregation aligned to confirmed bars."""
from __future__ import annotations

from datetime import datetime
import re
import numpy as np

from axes.axis1_dsl.indicators.indicators import CoreTALib


class MultiTimeframeError(ValueError): pass


class MultiTimeframeContext:
    def __init__(self, values): self.values = values

    @staticmethod
    def _minutes(timeframe):
        match = re.match(r"^(\d+)(m|h|d|w)$", str(timeframe))
        if not match: raise MultiTimeframeError(f"지원하지 않는 MTF 주기: {timeframe}")
        value, unit = int(match.group(1)), match.group(2)
        if value <= 0: raise MultiTimeframeError(f"MTF 주기는 1 이상이어야 합니다: {timeframe}")
        return value * {"m":1,"h":60,"d":1440,"w":10080}[unit]

    def _datetimes(self):
        result=[]
        for date, clock in zip(self.values["date"], self.values["time"]):
            date_text=f"{int(date):08d}"; clock_text=f"{int(clock):06d}"
            result.append(datetime.strptime(date_text+clock_text, "%Y%m%d%H%M%S"))
        return result

    def _buckets(self, timeframe):
        minutes=self._minutes(timeframe); result=[]
        for value in self._datetimes():
            epoch=int(value.timestamp()//60)
            result.append(epoch//minutes)
        return np.asarray(result, dtype=np.int64)

    def field(self, timeframe, field):
        if field not in {"open","high","low","close","volume"}: raise MultiTimeframeError(f"지원하지 않는 MTF 필드: {field}")
        buckets=self._buckets(timeframe); source=np.asarray(self.values[field],float)
        output=np.full(len(source),np.nan); current=None; aggregate=None; last_completed=np.nan
        for i,(bucket,value) in enumerate(zip(buckets,source)):
            if bucket!=current:
                if current is not None: last_completed=aggregate
                current=bucket; aggregate=value
            elif field=="high": aggregate=max(aggregate,value)
            elif field=="low": aggregate=min(aggregate,value)
            elif field=="volume": aggregate+=value
            elif field=="close": aggregate=value
            output[i]=last_completed
        return output

    def close(self,timeframe): return self.field(timeframe,"close")
    def open(self,timeframe): return self.field(timeframe,"open")
    def high(self,timeframe): return self.field(timeframe,"high")
    def low(self,timeframe): return self.field(timeframe,"low")
    def volume(self,timeframe): return self.field(timeframe,"volume")
    def sma(self,timeframe,period):
        confirmed=self.close(timeframe); buckets=self._buckets(timeframe)
        unique=[]; seen=set()
        for bucket,value in zip(buckets,confirmed):
            if bucket not in seen and np.isfinite(value): unique.append(value);seen.add(bucket)
        averages=CoreTALib.sma(np.asarray(unique,float),int(period)) if unique else np.asarray([])
        mapping={bucket:value for bucket,value in zip(sorted(seen),averages)}
        return np.asarray([mapping.get(bucket,np.nan) for bucket in buckets],float)
