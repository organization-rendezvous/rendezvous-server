from abc import ABC, abstractmethod
from app.models.document import Document


class BaseCollector(ABC):
    @abstractmethod
    def fetch(self, topic: str, period: str) -> list[Document]:
        pass