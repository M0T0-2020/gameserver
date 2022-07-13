import json
from lib2to3.pgen2.token import OP
import uuid
from enum import Enum, IntEnum
from typing import Optional, List

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound

from .db import engine
from .config import MAX_USER_COUNT


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
    room_id:str
    live_id:int
    joined_user_count:int
    max_user_count:int

    class Config:
        orm_mode = True

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

def create_room(host_token:str, live_id:int, select_difficulity:int):
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `room` (live_id, select_difficulity, member1) VALUES (:live_id, :select_difficulity, :member1)"
            ),
            {"live_id":live_id, "select_difficulity":select_difficulity, "member1":host_token},
        )
    return result.lastrowid

def _get_oom_member_cnt_rom_room_by_live_id(conn, live_id:int) -> List[Optional[RoomListElement]]:
    result = conn.execute(
        text("SELECT * FROM `room` WHERE `live_id`=:live_id"),
        {"live_id": live_id},
    )
    try:
        rows = result.all()
        room_info_list = []
        for row in rows:
            joined_user_count = sum([1 if row[f"member{i}"] is not None else 0 for i in range(1,5)])
            max_user_count = MAX_USER_COUNT
            room_info_list.append(
                RoomListElement(room_id=row["room_id"], live_id=row["live_id"],
                                joined_user_count=joined_user_count, max_user_count=max_user_count)
            )
        return room_info_list
    except NoResultFound:
        return None


def _insert_new_member(conn, room_id:int, member_num:int, token:str) -> int:
    try:
        result = conn.execute(
            text(f"UPDATE `room` SET `member{member_num}`=:member_token WHERE `room_id`=:room_id"),
            {"room_id": room_id, "member_token":token}
        )    
        return 1
    except NoResultFound:
        return None


def _join_as_room_member(conn, room_id:int, token: str) -> int:
    result = conn.execute(
        text("SELECT `member1`,`member2`,`member3`,`member4` FROM `room` WHERE `room_id`=:room_id"),
        {"room_id": room_id},
    )
    try:
        row = result.one()
        members = [row[f"member{i}"] for i in range(1,5) if row[f"member{i}"] is not None]
        joined_user_count = len(members)
        if joined_user_count < MAX_USER_COUNT and token not in members:
            new_member_num = joined_user_count + 1
            return _insert_new_member(conn, room_id, new_member_num, token)
        else:
            return 0
    except NoResultFound:
        return None

def list_room(live_id:int) -> List[RoomListElement]:
    room_info_list = []
    with engine.begin() as conn:
        room_info_list = _get_oom_member_cnt_rom_room_by_live_id(conn, live_id)

    return room_info_list

def join_room(room_id:str, token:str) -> int:
    with engine.begin() as conn:
        state = _join_as_room_member(conn, room_id, token)
    return state
