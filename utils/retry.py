"""
재시도 유틸리티
네트워크 요청 등 실패 가능한 작업의 자동 재시도.
"""
import time
import functools
from typing import Callable, Type
from utils.logger import log


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """
    재시도 데코레이터.

    Args:
        max_attempts: 최대 시도 횟수
        delay: 초기 대기 시간(초)
        backoff: 대기 시간 배율
        exceptions: 재시도할 예외 타입
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        log.warning(
                            f"{func.__name__} 실패 ({attempt}/{max_attempts}), "
                            f"{current_delay:.1f}초 후 재시도: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            log.error(f"{func.__name__} 최종 실패: {last_exception}")
            raise last_exception

        return wrapper
    return decorator
