from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, CHAR

from config.database import Base


class SysComment(Base):
    __tablename__ = 'sys_comment'
    __table_args__ = {'comment': '评论表'}

    comment_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='评论ID')
    user_id = Column(BigInteger, nullable=False, comment='评论用户ID')
    biz_type = Column(String(50), nullable=False, server_default='', comment='业务类型')
    biz_id = Column(String(64), nullable=False, server_default='', comment='业务对象ID')
    parent_id = Column(BigInteger, nullable=True, comment='父评论ID')
    root_id = Column(BigInteger, nullable=True, comment='根评论ID')
    reply_user_id = Column(BigInteger, nullable=True, comment='被回复用户ID')
    content = Column(Text, nullable=False, comment='评论内容')
    ip = Column(String(128), server_default='', comment='评论者IP')
    ip_location = Column(String(64), server_default='', comment='IP归属地')
    like_count = Column(Integer, nullable=False, server_default='0', comment='点赞数')
    reply_count = Column(Integer, nullable=False, server_default='0', comment='回复数')
    status = Column(Integer, nullable=False, server_default='1', comment='状态:0隐藏1正常2待审核')
    is_top = Column(Integer, nullable=False, server_default='0', comment='是否置顶')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志')
    create_by = Column(String(64), server_default='', comment='创建者')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), server_default='', comment='更新者')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    remark = Column(String(500), server_default='', comment='备注')


class SysCommentLike(Base):
    __tablename__ = 'sys_comment_like'
    __table_args__ = {'comment': '评论点赞表'}

    like_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='点赞ID')
    comment_id = Column(BigInteger, nullable=False, comment='评论ID')
    user_id = Column(BigInteger, nullable=False, comment='点赞用户ID')
    create_time = Column(DateTime, default=datetime.now, comment='点赞时间')
