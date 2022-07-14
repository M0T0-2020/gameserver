import json
import uuid
from enum import Enum, IntEnum
from typing import Optional, List, Tuple

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound

from .db import engine
from .config import MAX_USER_COUNT
from ResReqModel import LiveDifficulty, WaitRoomStatus, JoinRoomResult


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げる"""


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

    class Config:
        orm_mode = True

class RoomListElement(BaseModel):
    room_id:int
    live_id:int
    joined_user_count:int
    max_user_count:int

    class Config:
        orm_mode = True

class RoomUserListElement(BaseModel):
    user_id:int
    name:str
    leader_card_id:int
    select_difficulty: LiveDifficulty
    is_host:bool

def create_user(name: str, leader_card_id: int) -> str:
    """Create new user and returns their token"""
    token = str(uuid.uuid4())
    # NOTE: tokenが衝突したらリトライする必要がある.
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `user` (name, token, leader_card_id) VALUES (:name, :token, :leader_card_id)"
            ),
            {"name": name, "token": token, "leader_card_id": leader_card_id},
        )
        # print(result)
    return token


def _get_user_by_token(conn, token: str) -> Optional[SafeUser]:
    # TODO: 実装
    result = conn.execute(
        text("SELECT `id`, `name`, `leader_card_id` FROM `user` WHERE `token`=:token"),
        {"token": token},
    )
    try:
        row = result.one()
    except NoResultFound:
        return None
    return SafeUser.from_orm(row)

def get_user_by_token(token: str) -> Optional[SafeUser]:
    with engine.begin() as conn:
        return _get_user_by_token(conn, token)


def update_user(token: str, name: str, leader_card_id: int) -> None:
    # このコードを実装してもらう
    with engine.begin() as conn:
        # TODO: 実装
        try:
            _id = _get_user_by_token(conn, token).id
            conn.execute(
                text(
                    "UPDATE `user` SET name=:name, leader_card_id=:leader_card_id WHERE id=:id"
                ),
                {"name": name, "leader_card_id": leader_card_id, "id": _id},
            )
        except NoResultFound:
            return None

def create_room(host_token:str, live_id:int, select_difficulty:int):
    assert select_difficulty == 1 or select_difficulty == 2
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `room` (live_id, select_difficulty, member1) VALUES (:live_id, :select_difficulty, :member1)"
            ),
            {"live_id":live_id, "select_difficulty":select_difficulty, "member1":host_token},
        )
    return result.lastrowid

def _get_room_member_cnt_rom_room_by_live_id(conn, live_id:int) -> List[Optional[RoomListElement]]:
    result = conn.execute(
        text("SELECT * FROM `room` WHERE `live_id`=:live_id"),
        {"live_id": live_id},
    )
    try:
        rows = result.all()
        room_info_list = []
        for row in rows:
            joined_user_count = sum([1 if row[f"member{i}"] is not None else 0 for i in range(1,MAX_USER_COUNT + 1)])
            max_user_count = MAX_USER_COUNT
            room_info_list.append(
                RoomListElement(room_id=row["room_id"], live_id=row["live_id"],
                                joined_user_count=joined_user_count, max_user_count=max_user_count)
            )
        return room_info_list
    except NoResultFound:
        return None

def list_room(live_id:int) -> List[RoomListElement]:
    room_info_list = []
    with engine.begin() as conn:
        room_info_list = _get_room_member_cnt_rom_room_by_live_id(conn, live_id)
    return room_info_list

def _insert_new_member(conn, room_id:int, member_num:int, token:str) -> JoinRoomResult:
    try:
        conn.execute(
            text(f"UPDATE `room` SET `member{member_num}`=:member_token WHERE `room_id`=:room_id"),
            {"room_id": room_id, "member_token":token}
        )
        return JoinRoomResult.Ok
    except NoResultFound:
        return JoinRoomResult.OtherError

def _join_as_room_member(conn, room_id:int, token: str) -> int:
    try:
        result = conn.execute(
            text("SELECT `member1`,`member2`,`member3`,`member4` FROM `room` WHERE `room_id`=:room_id"),
            {"room_id": room_id},
        )
        row = result.one()
        members = [row[f"member{i}"] for i in range(1, MAX_USER_COUNT + 1) if row[f"member{i}"] is not None]
        absent_member_idx = [i for i in range(1, MAX_USER_COUNT + 1) if row[f"member{i}"] is None]
        joined_user_count = len(members)
        if joined_user_count == 0:
            # 解散
            return JoinRoomResult.Disbanded
        elif joined_user_count < MAX_USER_COUNT:
            if token not in members:
                # 空いてる席に追加
                return _insert_new_member(conn, room_id, absent_member_idx[0], token)
            else:
                return JoinRoomResult.Ok
        else:
            # RoomFull
            return JoinRoomResult.RoomFull
    except NoResultFound:
        return JoinRoomResult.OtherError

def join_room(room_id:int, token:str) -> int:
    with engine.begin() as conn:
        status = _join_as_room_member(conn, room_id, token)
    return status

def _get_user_info(conn, row) -> List[RoomUserListElement]:
    user_info_list = []
    select_difficulty = LiveDifficulty.Normal if row["select_difficulty"] == 1 else LiveDifficulty.Hard
    try:
        tokens = [row[f"member{i}"] for i in range(1,MAX_USER_COUNT + 1) if row[f"member{i}"] is not None]
        if len(tokens) == 0:
            # Dissolution
            return []
        result = conn.execute(
            text("SELECT `id`, `name`, `leader_card_id`, `token` FROM `user` WHERE `token` IN :tokens"),
            {"tokens": tokens}
        )
        member_rows = result.all()
        for row in member_rows:
            user_info_list.append(
                RoomUserListElement(
                    user_id=tokens.index(row["token"]), name=row["name"],
                    leader_card_id=row["leader_card_id"], select_difficulty=select_difficulty,
                    # ここのホストの部分はよく考える必要がある
                    is_host=row["token"] == tokens[0]
                )
            )
        return user_info_list
    except NoResultFound:
        return None

def _get_room_user_list(conn, room_id:str) -> List[RoomUserListElement]:
    try:
        result = conn.execute(
            text("SELECT `member1`,`member2`,`member3`,`member4`, `select_difficulty` FROM `room` WHERE `room_id`=:room_id"),
            {"room_id": room_id}
        )
        row = result.one()
        user_info_list = _get_user_info(conn, row)

        if len(user_info_list) == 0:
            # Dissolution
            status = WaitRoomStatus.Dissolution
        else:
            # Waiting
            status = WaitRoomStatus.Waiting
        """
        elif len(user_info_list) == MAX_USER_COUNT:
            # LiveStart
            status = 2
        """
        return status, user_info_list
    except NoResultFound:
        return None

def wait_room(room_id:int) -> Tuple[WaitRoomStatus, RoomUserListElement]:
    with engine.begin() as conn:
        status, room_user_list = _get_room_user_list(conn, room_id)
    return status, room_user_list
