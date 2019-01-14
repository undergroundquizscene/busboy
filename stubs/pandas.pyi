from typing import Any, Union, Dict
from numpy import ndarray

class DataFrame(object):
    def __getitem__(self, index: str) -> Any: ...
    def __setitem__(self, index: str, value: Any) -> None: ...
    def __init__(self,
            data: Union[ndarray, DataFrame, Dict[str, Any], None] = None,
        ) -> None: ...
