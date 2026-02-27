from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.user_do import SysUser
from module_comment.dao.comment_dao import CommentDao
from module_comment.entity.do.comment_do import SysComment
from module_comment.entity.vo.comment_vo import (
    CommentCreateVO, CommentItemVO, CommentListVO, CommentUserVO,
    CommentStatsVO, CommentAuditVO, CommentAdminQueryVO,
)
from module_comment.utils.filter_utils import xss_clean, sensitive_filter


class CommentService:

    @classmethod
    async def get_list(cls, db: AsyncSession, biz_type: str, biz_id: str,
                       page: int = 1, page_size: int = 20, sort: str = 'latest',
                       current_user_id: int = None):
        total, comments = await CommentDao.get_comment_list(db, biz_type, biz_id, page, page_size, sort)
        items = []
        for c in comments:
            user_row = await db.get(SysUser, c.user_id)
            user_vo = CommentUserVO(
                user_id=c.user_id,
                nick_name=user_row.nick_name if user_row else '',
                avatar=user_row.avatar if user_row else '',
            )
            replies_rows = await CommentDao.get_top_replies(db, c.comment_id, limit=3)
            replies = []
            for r in replies_rows:
                r_user = await db.get(SysUser, r.user_id)
                reply_user = None
                if r.reply_user_id:
                    ru = await db.get(SysUser, r.reply_user_id)
                    if ru:
                        reply_user = CommentUserVO(user_id=ru.user_id, nick_name=ru.nick_name, avatar=ru.avatar)
                is_liked = False
                if current_user_id:
                    like = await CommentDao.check_like(db, r.comment_id, current_user_id)
                    is_liked = like is not None
                replies.append(CommentItemVO(
                    comment_id=r.comment_id,
                    user=CommentUserVO(
                        user_id=r.user_id,
                        nick_name=r_user.nick_name if r_user else '',
                        avatar=r_user.avatar if r_user else '',
                    ),
                    reply_user=reply_user,
                    content=r.content,
                    ip_location=r.ip_location or '',
                    like_count=r.like_count,
                    is_liked=is_liked,
                    create_time=r.create_time,
                ))

            comment_liked = False
            if current_user_id:
                like = await CommentDao.check_like(db, c.comment_id, current_user_id)
                comment_liked = like is not None

            items.append(CommentItemVO(
                comment_id=c.comment_id,
                user=user_vo,
                content=c.content,
                ip_location=c.ip_location or '',
                like_count=c.like_count,
                reply_count=c.reply_count,
                is_liked=comment_liked,
                is_top=bool(c.is_top),
                create_time=c.create_time,
                replies=replies,
                has_more_replies=c.reply_count > 3,
            ))

        return CommentListVO(total=total, page=page, page_size=page_size, list=items)

    @classmethod
    async def create(cls, db: AsyncSession, req: CommentCreateVO, user_id: int,
                     user_name: str = '', ip: str = '', ip_location: str = ''):
        clean_content = xss_clean(req.content)
        clean_content = sensitive_filter(clean_content)
        if not clean_content:
            raise ValueError('评论内容不能为空')

        root_id = req.root_id
        if req.parent_id and not root_id:
            parent = await CommentDao.get_by_id(db, req.parent_id)
            if parent:
                root_id = parent.root_id or parent.comment_id

        comment = SysComment(
            user_id=user_id,
            biz_type=req.biz_type,
            biz_id=req.biz_id,
            parent_id=req.parent_id,
            root_id=root_id,
            reply_user_id=req.reply_user_id,
            content=clean_content,
            ip=ip,
            ip_location=ip_location,
            status=1,
            create_by=user_name,
        )
        comment = await CommentDao.insert(db, comment)
        if root_id:
            await CommentDao.incr_reply_count(db, root_id)
        await db.commit()
        return comment

    @classmethod
    async def update(cls, db: AsyncSession, comment_id: int, content: str, user_id: int):
        comment = await CommentDao.get_by_id(db, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        if comment.user_id != user_id:
            raise PermissionError('只能修改自己的评论')
        if comment.create_time and datetime.now() - comment.create_time > timedelta(hours=24):
            raise ValueError('超过24小时不可修改')

        clean_content = xss_clean(content)
        clean_content = sensitive_filter(clean_content)
        await CommentDao.update_content(db, comment_id, clean_content)
        await db.commit()

    @classmethod
    async def delete(cls, db: AsyncSession, comment_id: int, user_id: int):
        comment = await CommentDao.get_by_id(db, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        if comment.user_id != user_id:
            raise PermissionError('只能删除自己的评论')
        await CommentDao.soft_delete(db, comment_id)
        await db.commit()

    @classmethod
    async def toggle_like(cls, db: AsyncSession, comment_id: int, user_id: int):
        comment = await CommentDao.get_by_id(db, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        existing = await CommentDao.check_like(db, comment_id, user_id)
        if existing:
            await CommentDao.remove_like(db, comment_id, user_id)
            is_liked = False
        else:
            await CommentDao.add_like(db, comment_id, user_id)
            is_liked = True
        await db.commit()
        updated = await CommentDao.get_by_id(db, comment_id)
        return {'is_liked': is_liked, 'like_count': updated.like_count if updated else 0}

    @classmethod
    async def count(cls, db: AsyncSession, biz_type: str, biz_id: str):
        return await CommentDao.count_by_biz(db, biz_type, biz_id)

    @classmethod
    async def admin_audit(cls, db: AsyncSession, req: CommentAuditVO):
        await CommentDao.batch_audit(db, req.comment_ids, req.status, req.remark or '')
        await db.commit()

    @classmethod
    async def admin_delete(cls, db: AsyncSession, comment_id: int):
        await CommentDao.hard_delete(db, comment_id)
        await db.commit()

    @classmethod
    async def get_stats(cls, db: AsyncSession):
        data = await CommentDao.get_stats(db)
        return CommentStatsVO(**data)

    @classmethod
    async def admin_list(cls, db: AsyncSession, query: CommentAdminQueryVO):
        total, rows = await CommentDao.admin_list(
            db, status=query.status, biz_type=query.biz_type,
            content=query.content, begin_time=query.begin_time,
            end_time=query.end_time, page=query.page, page_size=query.page_size,
        )
        items = []
        for c in rows:
            user_row = await db.get(SysUser, c.user_id)
            items.append(CommentItemVO(
                comment_id=c.comment_id,
                user=CommentUserVO(
                    user_id=c.user_id,
                    nick_name=user_row.nick_name if user_row else '',
                    avatar=user_row.avatar if user_row else '',
                ),
                content=c.content,
                ip_location=c.ip_location or '',
                like_count=c.like_count,
                reply_count=c.reply_count,
                is_top=bool(c.is_top),
                create_time=c.create_time,
            ))
        return CommentListVO(total=total, page=query.page, page_size=query.page_size, list=items)
