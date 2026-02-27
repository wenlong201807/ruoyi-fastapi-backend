from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentCreateVO(BaseModel):
    biz_type: str = Field(..., max_length=50, description='业务类型')
    biz_id: str = Field(..., max_length=64, description='业务对象ID')
    content: str = Field(..., min_length=1, max_length=1000, description='评论内容')
    parent_id: Optional[int] = Field(None, description='父评论ID')
    root_id: Optional[int] = Field(None, description='根评论ID')
    reply_user_id: Optional[int] = Field(None, description='被回复用户ID')


class CommentUpdateVO(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description='评论内容')


class CommentQueryVO(BaseModel):
    biz_type: str = ''
    biz_id: str = ''
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=50)
    sort: str = Field('latest', pattern=r'^(latest|hottest)$')


class CommentAdminQueryVO(BaseModel):
    status: Optional[int] = None
    biz_type: Optional[str] = None
    user_name: Optional[str] = None
    content: Optional[str] = None
    begin_time: Optional[str] = None
    end_time: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class CommentAuditVO(BaseModel):
    comment_ids: list[int] = Field(..., min_length=1, max_length=100)
    status: int = Field(..., ge=0, le=2)
    remark: Optional[str] = Field(None, max_length=500)


class CommentUserVO(BaseModel):
    user_id: int
    nick_name: str = ''
    avatar: str = ''


class CommentItemVO(BaseModel):
    comment_id: int
    user: CommentUserVO
    reply_user: Optional[CommentUserVO] = None
    content: str
    ip_location: str = ''
    like_count: int = 0
    reply_count: int = 0
    is_liked: bool = False
    is_top: bool = False
    create_time: Optional[datetime] = None
    replies: list['CommentItemVO'] = []
    has_more_replies: bool = False


class CommentListVO(BaseModel):
    total: int
    page: int
    page_size: int
    list: list[CommentItemVO]


class CommentStatsVO(BaseModel):
    total: int = 0
    today_new: int = 0
    pending_audit: int = 0
    hidden: int = 0
