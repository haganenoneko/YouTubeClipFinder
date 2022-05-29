from typing import List 

class InvalidArgumentException(ValueError):
    def __init__(
        self, 
        parname: str, 
        val: str, 
        allowed: List[str]) -> None:
        super().__init__(
            f"`{parname}` must be one of {allowed}, not {val}"
        )

class NoSignalException(RuntimeError):
    def __init__(self) -> None:
        super().__init__("No signal found.")