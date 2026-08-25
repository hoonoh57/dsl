"""Deterministic OHLC broker emulator with explicit order lifecycle."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrderStatus(str,Enum):
    CREATED="CREATED";ACCEPTED="ACCEPTED";TRIGGERED="TRIGGERED";FILLED="FILLED"
    CANCELED="CANCELED";REJECTED="REJECTED";EXPIRED="EXPIRED"


@dataclass
class BrokerOrder:
    id:str; side:str; type:str="MARKET"; quantity:float=1.0
    limit_price:Optional[float]=None; stop_price:Optional[float]=None
    tif:str="GTC"; oco:Optional[str]=None; status:OrderStatus=OrderStatus.CREATED
    fill_price:Optional[float]=None; reason:Optional[str]=None


class BrokerEmulator:
    TYPES={"MARKET","LIMIT","STOP","STOP_LIMIT"}
    def __init__(self): self.orders={}
    def submit(self,order:BrokerOrder):
        order.type=order.type.upper();order.side=order.side.upper();order.tif=order.tif.upper()
        if order.id in self.orders: return self._reject(order,"duplicate id")
        if order.type not in self.TYPES:return self._reject(order,"unsupported order type")
        if order.quantity<=0:return self._reject(order,"quantity must be positive")
        if order.type in {"LIMIT","STOP_LIMIT"} and order.limit_price is None:return self._reject(order,"limit price required")
        if order.type in {"STOP","STOP_LIMIT"} and order.stop_price is None:return self._reject(order,"stop price required")
        order.status=OrderStatus.ACCEPTED;self.orders[order.id]=order;return order
    @staticmethod
    def _reject(order,reason):order.status=OrderStatus.REJECTED;order.reason=reason;return order
    def cancel(self,order_id,reason="user canceled"):
        order=self.orders[order_id]
        if order.status in {OrderStatus.ACCEPTED,OrderStatus.TRIGGERED}:
            order.status=OrderStatus.CANCELED;order.reason=reason
        return order
    def process_bar(self,open_,high,low,close,end_of_session=False):
        fills=[]
        for order in list(self.orders.values()):
            if order.status not in {OrderStatus.ACCEPTED,OrderStatus.TRIGGERED}:continue
            buy=order.side in {"BUY","COVER"};price=None
            if order.type=="MARKET":price=float(open_)
            elif order.type=="LIMIT" or order.status==OrderStatus.TRIGGERED:
                hit=low<=order.limit_price if buy else high>=order.limit_price
                if hit:price=min(float(open_),order.limit_price) if buy else max(float(open_),order.limit_price)
            elif order.type in {"STOP","STOP_LIMIT"}:
                hit=high>=order.stop_price if buy else low<=order.stop_price
                if hit:
                    if order.type=="STOP":price=max(float(open_),order.stop_price) if buy else min(float(open_),order.stop_price)
                    else:
                        order.status=OrderStatus.TRIGGERED
                        limit_hit=low<=order.limit_price if buy else high>=order.limit_price
                        if limit_hit:price=order.limit_price
            if price is not None:
                order.status=OrderStatus.FILLED;order.fill_price=float(price);fills.append(order)
                if order.oco:
                    for sibling in self.orders.values():
                        if sibling.id!=order.id and sibling.oco==order.oco:self.cancel(sibling.id,"OCO sibling filled")
            elif end_of_session and order.tif=="DAY":
                order.status=OrderStatus.EXPIRED;order.reason="DAY expired"
        return fills
