"""Small runtime primitives shared by data-pipeline steps."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class CallResult[T]:
    value: T | None = None
    error: Exception | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    def unwrap(self) -> T:
        if self.error is not None:
            raise self.error
        return cast(T, self.value)

    @classmethod
    def invoke(
        cls,
        operation: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> "CallResult[T]":
        try:
            return cls(value=operation(*args, **kwargs))
        except Exception as error:
            return cls(error=error)
