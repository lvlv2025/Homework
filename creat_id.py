from sqlalchemy.orm import sessionmaker, Session
import random
from db_model import Users_info,ChatHistory
import uuid

def generate_unique_user_uuid(db: Session, length: int = 11):
    """
    生成指定长度的唯一用户UUID数字字符串
    :param db: 数据库 Session
    :param length: UUID 数字长度，默认为 11
    :return: 唯一数字字符串
    """
    if length < 1:
        raise ValueError("长度必须大于0")

    while True:
        # 生成指定长度的数字UUID
        start = 10**(length - 1)
        end = 10**length - 1
        user_uuid = str(random.randint(start, end))

        # 查询数据库是否已存在
        exists = db.query(Users_info).filter_by(user_uuid=user_uuid).first()
        if not exists:
            return user_uuid


def generate_topic_id(db: Session, user_uuid: str) -> str:
    """
    生成唯一的 topic_id，并绑定 user_uuid
    """
    while True:
        topic_id = str(uuid.uuid4())  # 36位全局唯一ID
        exists = db.query(ChatHistory).filter_by(user_uuid=user_uuid, topic_id=topic_id).first()
        if not exists:
            return topic_id

