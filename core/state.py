"""Deterministic causal state primitives shared by batch and streaming runtimes."""
from __future__ import annotations
import numpy as np

class CoreStateLib:
    @staticmethod
    def _bool(values): return np.asarray(values,dtype=bool)

    @classmethod
    def edge(cls,condition):
        source=cls._bool(condition);result=np.zeros(len(source),dtype=bool)
        if len(source): result[0]=source[0]
        if len(source)>1: result[1:]=source[1:] & ~source[:-1]
        return result

    @classmethod
    def falling_edge(cls,condition):
        source=cls._bool(condition);result=np.zeros(len(source),dtype=bool)
        if len(source)>1: result[1:]=~source[1:] & source[:-1]
        return result

    @classmethod
    def ready_after(cls,trigger,bars):
        """False on a trigger and for ``bars`` subsequent bars."""
        source=cls._bool(trigger);bars=max(int(bars),0);result=np.ones(len(source),dtype=bool);remaining=0
        for i,hit in enumerate(source):
            if hit: remaining=bars+1
            result[i]=remaining==0
            if remaining: remaining-=1
        return result

    @classmethod
    def hold(cls,condition,bars):
        """Keep a condition true for the trigger bar plus N following bars."""
        source=cls._bool(condition);bars=max(int(bars),0);result=np.zeros(len(source),dtype=bool);remaining=0
        for i,hit in enumerate(source):
            if hit: remaining=bars+1
            result[i]=remaining>0
            if remaining: remaining-=1
        return result

    @classmethod
    def persist(cls,condition,bars):
        """True after condition has remained true for N consecutive bars."""
        source=cls._bool(condition);bars=max(int(bars),1);result=np.zeros(len(source),dtype=bool);count=0
        for i,hit in enumerate(source):
            count=count+1 if hit else 0;result[i]=count>=bars
        return result

    @classmethod
    def latch(cls,set_condition,reset_condition,initial=False):
        set_values,reset_values=cls._bool(set_condition),cls._bool(reset_condition)
        if len(set_values)!=len(reset_values): raise ValueError("latch 조건 배열 길이가 다릅니다.")
        result=np.zeros(len(set_values),dtype=bool);state=bool(initial)
        for i in range(len(result)):
            if reset_values[i]: state=False
            elif set_values[i]: state=True
            result[i]=state
        return result

    @classmethod
    def count(cls,condition,reset_condition):
        values,resets=cls._bool(condition),cls._bool(reset_condition)
        if len(values)!=len(resets): raise ValueError("count 조건 배열 길이가 다릅니다.")
        result=np.zeros(len(values),dtype=float);count=0
        for i in range(len(result)):
            if resets[i]: count=0
            elif values[i]: count+=1
            result[i]=count
        return result

    @classmethod
    def regime(cls,bullish,bearish,initial=0):
        up,down=cls._bool(bullish),cls._bool(bearish)
        if len(up)!=len(down): raise ValueError("regime 조건 배열 길이가 다릅니다.")
        result=np.zeros(len(up),dtype=float);state=int(initial)
        if state not in {-1,0,1}: raise ValueError("regime initial은 -1, 0, 1이어야 합니다.")
        for i in range(len(result)):
            if up[i] and not down[i]: state=1
            elif down[i] and not up[i]: state=-1
            result[i]=state
        return result
