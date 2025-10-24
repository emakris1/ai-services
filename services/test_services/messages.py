import datetime
import msgspec
import uuid


class Foo(msgspec.Struct):
    id: uuid.UUID
    datetime: datetime.datetime
    data: str = "foo"


class Bar(msgspec.Struct):
    id: uuid.UUID
    datetime: datetime.datetime
    data: str = "bar"
