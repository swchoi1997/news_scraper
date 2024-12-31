from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Callable, List


class Executor(ABC):
    @abstractmethod
    def execute(self, command: Callable):
        pass

class ExecutorService(Executor, ABC):
    @abstractmethod
    def shutdown(self) -> None:
        pass

    @abstractmethod
    def isShutdown(self) -> bool:
        pass

    @abstractmethod
    def isTerminated(self) -> bool:
        pass

    @abstractmethod
    def submit(self, command: Callable) -> Future:
        pass

    def invokeAll(self, command: List[Callable]) -> List[Future]:
        pass









class ThreadManager(Executor, ABC):

    def execute(self, command: Callable):
        pass