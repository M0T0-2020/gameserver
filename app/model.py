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


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げる"""


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

    class Config:
        orm_mode = True

class Room(BaseModel):
    """Room Data"""

    id: int
    room_id: str
    live_id: int
    select_difficulity: int

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
    room_id = str(uuid.uuid4())
    with engine.begin() as conn:
        result_create = conn.execute(
            text(
                "INSERT INTO `room` (room_id, live_id, select_difficulity) VALUES (:room_id, :live_id, :select_difficulity)"
            ),
            {"room_id": room_id, "live_id":live_id, "select_difficulity":select_difficulity},
        )
        result_join = conn.execute(
            text(
                "INSERT INTO `room_member` (room_id, member1) VALUES (:room_id, :member1)"
            ),
            {"room_id":room_id, "member1":host_token}
        )
    return room_id

def _get_columns_from_room_by_live_id(conn, live_id:int) -> List[Optional[Room]]:
    result = conn.execute(
        text("SELECT * FROM `room` WHERE `live_id`=:live_id"),
        {"live_id": live_id},
    )
    try:
        rows = result.all()
        info = [Room.from_orm(row) for row in rows]
        return info
    except NoResultFound:
        return None

def _get_room_member_cnt_from_room_member_by_room_id(conn, room_id:str) -> int:
    result = conn.execute(
        text("SELECT `member1`,`member2`,`member3`,`member4` FROM `room_member` WHERE `room_id`=:room_id"),
        {"room_id": room_id},
    )
    try:
        row = result.one()
        joined_user_count = sum([1 if row[f"member{i}"] is not None else 0 for i in range(1,5)])
        return joined_user_count
    except NoResultFound:
        return None

def _get_room_member_info_from_room_member_by_room_id_select_difficulty(conn, room_id:str, select_difficulty:int) -> int:
    result = conn.execute(
        text("SELECT `member1`,`member2`,`member3`,`member4` FROM `room_member` WHERE `room_id`=:room_id AND `select_difficulty`=:select_difficulty "),
        {"room_id": room_id, "select_difficulty":select_difficulty},
    )
    try:
        row = result.one()
        joined_user_count = sum([1 if row[f"member{i}"] is not None else 0 for i in range(1,5)])
        return joined_user_count
    except NoResultFound:
        return None


def list_room(live_id:int) -> List[RoomListElement]:
    room_info_list = []
    with engine.begin() as conn:
        room_info = _get_columns_from_room_by_live_id(conn, live_id)
        for r_i in room_info:
            room_id = r_i.room_id
            joined_user_count = _get_room_member_cnt_from_room_member_by_room_id(conn, room_id)
            max_user_count = 4
            room_info_list.append(
                RoomListElement(room_id=room_id, live_id=r_i.live_id, 
                                joined_user_count=joined_user_count, max_user_count=max_user_count)
            )
    return room_info_list

def join_room(room_id:str, select_difficulty:int) -> int:
    with engine.begin() as conn:
        member_cnt = _get_room_member_info_from_room_member_by_room_id_select_difficulty(conn, room_id, select_difficulty)
        if member_cnt < 4:

            return 1
        else:
            return 0
