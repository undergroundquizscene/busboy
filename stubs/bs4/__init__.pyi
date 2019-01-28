from typing import Any, Callable, Dict, List, Optional, Union

from bs4.element import Tag

class BeautifulSoup(Tag):
    def __init__(
        self, markup: str = "", features: Optional[str] = None, **kwargs: Any
    ) -> None: ...

class ResultSet(List[Tag]): ...
