from enum import Enum

from pydantic import BaseModel

# Request(BaseModel):
# Response(BaseModel):


class LiveDifficulty(Enum):
    Normal = 1
    Hard = 2


class JoinRoomResult(Enum):
    # 入場OK
    Ok = 1
    # 満員
    RoomFull = 2
    # 解散済み
    Disbanded = 3
    # その他エラー
    OtherError = 4


class WaitRoomStatus(Enum):
    # ホストがライブ開始ボタン押すのを待っている
    Waiting = 1
    # ライブ画面遷移OK
    LiveStart = 2
    # 解散された
    Dissolution = 3


class RoomInfo(BaseModel):
    room_id: int
    live_id: int
    joined_user_count: int
    max_user_count: int

    class Config:
        orm_mode = True


class RoomUser(BaseModel):
    user_id: int
    name: str
    leader_card_id: int
    select_difficulty: LiveDifficulty
    is_me: bool
    is_host: bool


class ResultUser(BaseModel):
    user_id: int
    judge_count_list: list[int]
    score: int


class UserCreateRequest(BaseModel):
    user_name: str
    leader_card_id: int


class UserCreateResponse(BaseModel):
    user_token: str


class RoomCreateRequest(BaseModel):
    live_id: int
    select_difficulty: LiveDifficulty


class RoomCreateResponse(BaseModel):
    room_id: int


class RoomListRequest(BaseModel):
    live_id: int


class RoomListResponse(BaseModel):
    room_info_list: list[RoomInfo]


class RoomJoinRequest(BaseModel):
    room_id: int
    select_difficulty: LiveDifficulty


class RoomJoinResponse(BaseModel):
    join_room_result: JoinRoomResult


class RoomWaitRequest(BaseModel):
    room_id: int


class RoomWaitResponse(BaseModel):
    status: WaitRoomStatus
    room_user_list: list[RoomUser]


class RoomStartRequest(BaseModel):
    room_id: int


class RoomStartResponse(BaseModel):
    pass


class RoomEndRequest(BaseModel):
    room_id: int
    # paefect, great, good, bad, missの順
    judge_count_list: list[int]
    score: int


class RoomEndResponse(BaseModel):
    pass


class RoomResultRequest(BaseModel):
    room_id: int


class RoomResultResponse(BaseModel):
    result_user_list: list[ResultUser]


class RoomLeaveRequest(BaseModel):
    room_id: int


class RoomLeaveResponse(BaseModel):
    pass
