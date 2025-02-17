import stat
from enum import Enum
from select import select

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from . import model
from .model import SafeUser
from .ResReqModel import (
    RoomCreateRequest,
    RoomCreateResponse,
    RoomEndRequest,
    RoomEndResponse,
    RoomJoinRequest,
    RoomJoinResponse,
    RoomLeaveRequest,
    RoomLeaveResponse,
    RoomListRequest,
    RoomListResponse,
    RoomResultRequest,
    RoomResultResponse,
    RoomStartRequest,
    RoomStartResponse,
    RoomWaitRequest,
    RoomWaitResponse,
    UserCreateRequest,
    UserCreateResponse,
)

app = FastAPI()

# Sample APIs


@app.get("/")
async def root():
    return {"message": "Hello World"}


# User APIs
@app.post("/user/create", response_model=UserCreateResponse)
def user_create(req: UserCreateRequest):
    """新規ユーザー作成"""
    token = model.create_user(req.user_name, req.leader_card_id)
    return UserCreateResponse(user_token=token)


bearer = HTTPBearer()


def get_auth_token(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    assert cred is not None
    if not cred.credentials:
        raise HTTPException(status_code=401, detail="invalid credential")
    return cred.credentials


@app.get("/user/me", response_model=SafeUser)
def user_me(token: str = Depends(get_auth_token)):
    user = model.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=404)
    # print(f"user_me({token=}, {user=})")
    return user


class Empty(BaseModel):
    pass


@app.post("/user/update", response_model=Empty)
def update(req: UserCreateRequest, token: str = Depends(get_auth_token)):
    """Update user attributes"""
    # print(req)
    model.update_user(token, req.user_name, req.leader_card_id)
    return {}


@app.post("/room/create", response_model=RoomCreateResponse)
def room_create(req: RoomCreateRequest, token: str = Depends(get_auth_token)):
    room_id = model.create_room(token, req.live_id, req.select_difficulty)
    return RoomCreateResponse(room_id=room_id)


@app.post("/room/list", response_model=RoomListResponse)
def room_list(req: RoomListRequest):
    room_info_list = model.list_room(req.live_id)
    return RoomListResponse(room_info_list=room_info_list)


@app.post("/room/join", response_model=RoomJoinResponse)
def room_join(req: RoomJoinRequest, token: str = Depends(get_auth_token)):
    join_room_result = model.join_room(req.room_id, req.select_difficulty, token)
    return RoomJoinResponse(join_room_result=join_room_result)


@app.post("/room/wait", response_model=RoomWaitResponse)
def room_wait(req: RoomWaitRequest, token: str = Depends(get_auth_token)):
    status, room_user_list = model.wait_room(req.room_id, token)
    return RoomWaitResponse(status=status, room_user_list=room_user_list)


@app.post("/room/start", response_model=RoomStartResponse)
def room_start(req: RoomStartRequest, token: str = Depends(get_auth_token)):
    model.start_room(req.room_id, token)
    return RoomStartResponse()


@app.post("/room/end", response_model=RoomEndResponse)
def room_end(req: RoomEndRequest, token: str = Depends(get_auth_token)):
    model.end_room(req.room_id, req.score, req.judge_count_list, token)
    return RoomEndResponse()


@app.post("/room/result", response_model=RoomResultResponse)
def room_result(req: RoomResultRequest):
    print(req.room_id)
    result_user_list = model.result_room(req.room_id)
    return RoomResultResponse(result_user_list=result_user_list)


@app.post("/room/leave", response_model=RoomLeaveResponse)
def room_leave(req: RoomLeaveRequest, token: str = Depends(get_auth_token)):
    model.leave_room(req.room_id, token)
    return RoomEndResponse()
