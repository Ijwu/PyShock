from enum import Enum

class UserLookupType(Enum):
    ID = "id"
    Name = "name"

class BanLookupType(Enum):
    Name = "name"
    IP = "ip"