from pydantic import BaseModel
from typing import List
from .model import RoomListElement, RoomUserListElement

# Request(BaseModel):
# Response(BaseModel):

class UserCreateRequest(BaseModel):
    user_name: str
    leader_card_id: int

class UserCreateResponse(BaseModel):
    user_token: str


class RoomCreateRequest(BaseModel):
    live_id:int
    select_difficulty:int

class RoomCreateResponse(BaseModel):
    room_id:str

class RoomListRequest(BaseModel):
    live_id:int

class RoomListResponse(BaseModel):
    room_info_list:List[RoomListElement]

class RoomJoinRequest(BaseModel):
    room_id:str
    select_difficulty:int

class RoomJoinResponse(BaseModel):
    join_room_result:int

class RoomWaitRequest(BaseModel):
    room_id:str

class RoomWaitResponse(BaseModel):
    status:int
    room_user_list:List[RoomUserListElement]
