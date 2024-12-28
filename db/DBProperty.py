from abc import abstractmethod, ABC

from db.DBType import DBType


class DBProperty(ABC):
    def __init__(self, db_type: DBType):
        self.db_type = db_type

    @abstractmethod
    def connectionInfo(self) -> str:
        pass

    def getDBType(self):
        return self.db_type


class MysqlDBProperty(DBProperty, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(DBType.MYSQL)
        self.args = args
        self.kwargs = kwargs

    def connectionInfo(self):
        return ""

