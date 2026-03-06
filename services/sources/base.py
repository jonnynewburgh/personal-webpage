from abc import ABC, abstractmethod
from models.schemas import DatasetResult


class DataSource(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[DatasetResult]:
        ...
