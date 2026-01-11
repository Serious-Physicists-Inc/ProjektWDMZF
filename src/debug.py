# python internals
from __future__ import annotations
from typing import Callable, Any
from functools import wraps
import time

def debug_time(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"Elapsed time of {func.__name__}: {elapsed:.6f}s")
        return result
    return wrapper

__all__ = ['debug_time',]