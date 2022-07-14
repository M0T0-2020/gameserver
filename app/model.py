import json
from lib2to3.pgen2.token import RPAR
import uuid
from enum import Enum, IntEnum
from typing import Optional, Tuple

from fastapi import HTTPException
from pydantic import BaseModel
from pyparsing import Opt
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from urllib3 import Retry

from .config import MAX_USER_COUNT
from .db import engine
from .ResReqModel import (
    JoinRoomResult,
    LiveDifficulty,
    ResultUser,
    RoomInfo,
    RoomUser,
    WaitRoomStatus,
)


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げる"""


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

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

def _insert_member(conn, room_id, user_id):
    try:
        conn.execute(
            text(
                "INSERT INTO `member` (room_id, member_id) VALUES (:room_id, :user_id)"
            ),
            {
                "room_id": room_id,
                "user_id": user_id,
            },
        )
    except NoResultFound:
        return None

def create_room(host_token: str, live_id: int, select_difficulty: LiveDifficulty):
    assert (
        select_difficulty == LiveDifficulty.Normal
        or select_difficulty == LiveDifficulty.Hard
    )
    with engine.begin() as conn:
        user_id = _get_user_by_token(conn, host_token).id
        result = conn.execute(
            text(
                "INSERT INTO `room` (live_id, select_difficulty, status, owner) VALUES (:live_id, :select_difficulty, :status, :owner)"
            ),
            {
                "live_id": live_id,
                "select_difficulty": select_difficulty.value,
                "status": WaitRoomStatus.Waiting.value,
                "owner": user_id,
            },
        )

        room_id = result.lastrowid
        _insert_member(conn, room_id, user_id)
    return room_id


def _get_room_member_cnt_rom_room_by_live_id(
    conn, live_id: int
) -> list[Optional[RoomInfo]]:
    try:
        result = conn.execute(
            text(
                """
                SELECT room.room_id, status, live_id,  COUNT(member_id) AS joined_user_count
                FROM member
                INNER JOIN room ON member.room_id=room.room_id
                WHERE room.live_id=:live_id GROUP BY room.room_id
                """
            ),
            {"live_id": live_id}
        )
        rows = result.all()
        can_show = lambda room_status: room_status != WaitRoomStatus.Dissolution and room_status != WaitRoomStatus.LiveStart
        room_info_list = [
            RoomInfo(
                room_id=row["room_id"],
                live_id=row["live_id"],
                joined_user_count=row["joined_user_count"],
                max_user_count=MAX_USER_COUNT,
            ) for row in rows if can_show(WaitRoomStatus(row["status"]))
        ]
        return room_info_list
    except NoResultFound:
        return None

def list_room(live_id: int) -> list[RoomInfo]:
    room_info_list = []
    with engine.begin() as conn:
        room_info_list = _get_room_member_cnt_rom_room_by_live_id(conn, live_id)
    return room_info_list

def _join_as_room_member(conn, room_id: int, token: str) -> int:
    try:
        user_id = _get_user_by_token(conn, token).id
        result = conn.execute(
            text(
                """
                SELECT COUNT(member_id) AS joined_user_count
                FROM `member` WHERE `room_id`=:room_id
                """
            ),
            {"room_id": room_id},
        )
        row = result.one()
        joined_user_count = row["joined_user_count"]
        if joined_user_count == 0:
            # 解散
            return JoinRoomResult.Disbanded
        elif joined_user_count < MAX_USER_COUNT:
            try:
                conn.execute(
                    text(
                        "INSERT INTO `member` (room_id, member_id) VALUES (:room_id, :user_id)"
                    ),
                    {
                            "room_id": room_id,
                            "user_id": user_id,
                    }
                )
                return JoinRoomResult.Ok
            except NoResultFound:
                return JoinRoomResult.OtherError
        else:
            # RoomFull
            return JoinRoomResult.RoomFull
    except NoResultFound:
        return JoinRoomResult.OtherError


def join_room(room_id: int, token: str) -> int:
    with engine.begin() as conn:
        status = _join_as_room_member(conn, room_id, token)
    return status


def _get_user_info(conn, rows, req_user_id) -> Tuple[WaitRoomStatus, list[RoomUser]]:
    user_info_list = []
    status = WaitRoomStatus(rows[0]["status"])
    host_user_id = rows[0]["owner"]
    select_difficulty = LiveDifficulty(rows[0]["select_difficulty"])    
    for row in rows:
        user_info_list.append(
            RoomUser(
                user_id=row["member_id"],
                name=row["name"],
                leader_card_id=row["leader_card_id"],
                select_difficulty=select_difficulty,
                is_me=row["member_id"] == req_user_id,
                is_host=row["member_id"] == host_user_id,
            )
        )
    return status, user_info_list

def _get_room_user_list(
    conn, room_id: str, token: str
) -> Tuple[WaitRoomStatus, list[RoomUser]]:
    try:
        req_user_id = _get_user_by_token(conn, token).id
        result = conn.execute(
            text(
                """
                SELECT member_id, user.name, user.leader_card_id, room.select_difficulty, room.owner, room.status
                FROM member
                INNER JOIN user
                ON member.member_id=user.id
                INNER JOIN room
                ON member.room_id=room.room_id
                WHERE member.room_id=:room_id
                """
            ),
            {"room_id": room_id},
        )
        rows = result.all()
        status, user_info_list = _get_user_info(conn, rows, req_user_id)
        return status, user_info_list
    except NoResultFound:
        return None


def wait_room(room_id: int, token: str) -> Tuple[WaitRoomStatus, list[RoomUser]]:
    with engine.begin() as conn:
        status, room_user_list = _get_room_user_list(conn, room_id, token)
    return status, room_user_list


def start_room(room_id: int, token: str) -> None:
    with engine.begin() as conn:
        try:
            user_id = _get_user_by_token(conn, token).id
            result = conn.execute(
                text(
                    "SELECT `owner` FROM `room` WHERE `room_id`=:room_id"
                ),
                {"room_id": room_id},
            )
            row = result.one()
            if user_id == row["owner"]:
                result = conn.execute(
                    text("UPDATE `room` SET `status`=:status WHERE `room_id`=:room_id"),
                    {"status": WaitRoomStatus.LiveStart.value, "room_id": room_id},
                )
            else:
                print("owner is diffrent!!")
                raise Exception
        except NoResultFound as e:
            raise e

def _update_myresult_by_user_id(
    conn, room_id: int, user_id: int, score: int, judge_count_list: list[int]
):
    try:
        judge_count_join = ", ".join(map(str, judge_count_list))
        conn.execute(
            text(
                """
                UPDATE `member`
                SET score=:score, judge_count_list=:judge_count
                WHERE room_id=:room_id AND member_id=:user_id
                """
            ),
            {"room_id": room_id, "user_id": user_id, "score": score, "judge_count": judge_count_join},
        )
    except NoResultFound:
        return None


def end_room(room_id: int, score: int, judge_count_list: list[int], token) -> None:
    with engine.begin() as conn:
        user_id = _get_user_by_token(conn, token).id
        _update_myresult_by_user_id(
            conn, room_id, user_id, score, judge_count_list
        )


def check_can_return(rows):
    for row in rows:
        if row["score"] is None:
            return False
    return True

def _get_result_user_list_from_row(rows) -> list[ResultUser]:
    if not check_can_return(rows):
        return []
    resultuser_list = []
    for row in rows:
        u_id, score, judge_count_list = row["member_id"], row["score"], row["judge_count_list"]
        judge_count_list = list(map(int, judge_count_list.split(", ")))
        resultuser_list.append(
            ResultUser(user_id=u_id, judge_count_list=judge_count_list, score=score)
        )
    return resultuser_list


def _get_result_user_list(conn, room_id) -> list[ResultUser]:
    try:
        result = conn.execute(
            text(
                """
                SELECT member_id, judge_count_list, score
                FROM member
                WHERE room_id=:room_id
                """
            ),
            {"room_id": room_id},
        )
        rows = result.all()
        return _get_result_user_list_from_row(rows)
    except NoResultFound:
        return None


def result_room(room_id: int) -> None:
    with engine.begin() as conn:
        result_user_list = _get_result_user_list(conn, room_id)
    return result_user_list


def _sample_room_member_id(conn, room_id: int, leave_room_user_id: int):
    try:
        result = conn.execute(
            text(
                "SELECT `member1`,`member2`,`member3`,`member4` FROM `room` WHERE `room_id`=:room_id"
            ),
            {"room_id": room_id},
        )
        row = result.one()
        for i in range(1, MAX_USER_COUNT + 1):
            if (i != leave_room_user_id) and (row[f"member{i}"] is not None):
                return row[f"member{i}"]
        return "none"
    except NoResultFound:
        return None


def _leave_room_by_user_id(conn, room_id: int, leave_room_user_id: int, is_owner: bool):
    try:
        if is_owner:
            new_owner = _sample_room_member_id(conn, room_id, leave_room_user_id)
            print(f"new_owner {new_owner}")
            if new_owner != "none":
                conn.execute(
                    text(
                        f"UPDATE `room` SET member{leave_room_user_id}=NULL, owner=:new_owner WHERE room_id=:room_id"
                    ),
                    {"room_id": room_id, "new_owner": new_owner},
                )
            else:
                # status -> 解散
                conn.execute(
                    text(
                        "UPDATE `room` SET status=:dissolution WHERE room_id=:room_id"
                    ),
                    {
                        "room_id": room_id,
                        "dissolution": WaitRoomStatus.Dissolution.value,
                    },
                )
        else:
            conn.execute(
                text(
                    f"UPDATE `room` SET member{leave_room_user_id}=NULL WHERE room_id=:room_id"
                ),
                {"room_id": room_id},
            )
    except NoResultFound as e:
        raise e
        # return None


def _get_room_user_id_from_room(conn, room_id: int, token: str) -> Tuple[int, bool]:
    try:
        user_id = _get_user_by_token(conn, token).id
        result = conn.execute(
            text(
                "SELECT `member1`,`member2`,`member3`,`member4`, `owner` FROM `room` WHERE `room_id`=:room_id"
            ),
            {"room_id": room_id},
        )
        row = result.one()
        for i in range(1, 1 + MAX_USER_COUNT):
            if user_id == row[f"member{i}"]:
                return i, user_id == row["owner"]
    except NoResultFound:
        return None
    return None


def leave_room(room_id: int, token: str) -> None:
    with engine.begin() as conn:
        room_user_id, is_owner = _get_room_user_id_from_room(conn, room_id, token)
        _leave_room_by_user_id(conn, room_id, room_user_id, is_owner)
