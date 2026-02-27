from datetime import datetime, timedelta

from sqlalchemy import and_, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from module_comment.entity.do.comment_do import SysComment, SysCommentLike


class CommentDao:

    @classmethod
    async def get_comment_list(cls, db: AsyncSession, biz_type: str, biz_id: str,
                                page: int, page_size: int, sort: str = 'latest'):
        query = select(SysComment).where(
            and_(
                SysComment.biz_type == biz_type,
                SysComment.biz_id == biz_id,
                SysComment.parent_id.is_(None),
                SysComment.status == 1,
                SysComment.del_flag == '0',
            )
        )
        if sort == 'hottest':
            query = query.order_by(SysComment.is_top.desc(), SysComment.like_count.desc())
        else:
            query = query.order_by(SysComment.is_top.desc(), SysComment.create_time.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
        return total, rows

    @classmethod
    async def get_replies(cls, db: AsyncSession, root_id: int, page: int, page_size: int):
        query = select(SysComment).where(
            and_(
                SysComment.root_id == root_id,
                SysComment.parent_id.isnot(None),
                SysComment.status == 1,
                SysComment.del_flag == '0',
            )
        ).order_by(SysComment.create_time.asc())

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
        return total, rows

    @classmethod
    async def get_top_replies(cls, db: AsyncSession, root_id: int, limit: int = 3):
        query = select(SysComment).where(
            and_(
                SysComment.root_id == root_id,
                SysComment.parent_id.isnot(None),
                SysComment.status == 1,
                SysComment.del_flag == '0',
            )
        ).order_by(SysComment.create_time.asc()).limit(limit)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def get_by_id(cls, db: AsyncSession, comment_id: int):
        return (await db.execute(
            select(SysComment).where(SysComment.comment_id == comment_id)
        )).scalar_one_or_none()

    @classmethod
    async def insert(cls, db: AsyncSession, comment: SysComment):
        db.add(comment)
        await db.flush()
        await db.refresh(comment)
        return comment

    @classmethod
    async def update_content(cls, db: AsyncSession, comment_id: int, content: str, update_by: str = ''):
        await db.execute(
            update(SysComment).where(SysComment.comment_id == comment_id).values(
                content=content, update_by=update_by, update_time=datetime.now()
            )
        )

    @classmethod
    async def soft_delete(cls, db: AsyncSession, comment_id: int):
        await db.execute(
            update(SysComment).where(SysComment.comment_id == comment_id).values(del_flag='1')
        )
        await db.execute(
            update(SysComment).where(SysComment.root_id == comment_id).values(del_flag='1')
        )

    @classmethod
    async def hard_delete(cls, db: AsyncSession, comment_id: int):
        await db.execute(delete(SysComment).where(SysComment.comment_id == comment_id))
        await db.execute(delete(SysComment).where(SysComment.root_id == comment_id))
        await db.execute(delete(SysCommentLike).where(SysCommentLike.comment_id == comment_id))

    @classmethod
    async def batch_audit(cls, db: AsyncSession, comment_ids: list[int], status: int, remark: str = ''):
        await db.execute(
            update(SysComment).where(SysComment.comment_id.in_(comment_ids)).values(
                status=status, remark=remark, update_time=datetime.now()
            )
        )

    @classmethod
    async def incr_reply_count(cls, db: AsyncSession, root_id: int):
        await db.execute(
            update(SysComment).where(SysComment.comment_id == root_id).values(
                reply_count=SysComment.reply_count + 1
            )
        )

    @classmethod
    async def count_by_biz(cls, db: AsyncSession, biz_type: str, biz_id: str):
        result = await db.execute(
            select(func.count()).where(
                and_(
                    SysComment.biz_type == biz_type,
                    SysComment.biz_id == biz_id,
                    SysComment.status == 1,
                    SysComment.del_flag == '0',
                )
            )
        )
        return result.scalar() or 0

    @classmethod
    async def get_stats(cls, db: AsyncSession):
        total = (await db.execute(
            select(func.count()).where(SysComment.del_flag == '0')
        )).scalar() or 0

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new = (await db.execute(
            select(func.count()).where(
                and_(SysComment.del_flag == '0', SysComment.create_time >= today_start)
            )
        )).scalar() or 0

        pending = (await db.execute(
            select(func.count()).where(
                and_(SysComment.del_flag == '0', SysComment.status == 2)
            )
        )).scalar() or 0

        hidden = (await db.execute(
            select(func.count()).where(
                and_(SysComment.del_flag == '0', SysComment.status == 0)
            )
        )).scalar() or 0

        return {'total': total, 'today_new': today_new, 'pending_audit': pending, 'hidden': hidden}

    @classmethod
    async def admin_list(cls, db: AsyncSession, status=None, biz_type=None,
                         user_name=None, content=None, begin_time=None, end_time=None,
                         page=1, page_size=20):
        query = select(SysComment).where(SysComment.del_flag == '0')
        if status is not None:
            query = query.where(SysComment.status == status)
        if biz_type:
            query = query.where(SysComment.biz_type == biz_type)
        if content:
            query = query.where(SysComment.content.like(f'%{content}%'))
        if begin_time:
            query = query.where(SysComment.create_time >= begin_time)
        if end_time:
            query = query.where(SysComment.create_time <= end_time)
        query = query.order_by(SysComment.create_time.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0
        offset = (page - 1) * page_size
        rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
        return total, rows

    @classmethod
    async def check_like(cls, db: AsyncSession, comment_id: int, user_id: int):
        result = await db.execute(
            select(SysCommentLike).where(
                and_(SysCommentLike.comment_id == comment_id, SysCommentLike.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def add_like(cls, db: AsyncSession, comment_id: int, user_id: int):
        db.add(SysCommentLike(comment_id=comment_id, user_id=user_id))
        await db.execute(
            update(SysComment).where(SysComment.comment_id == comment_id).values(
                like_count=SysComment.like_count + 1
            )
        )

    @classmethod
    async def remove_like(cls, db: AsyncSession, comment_id: int, user_id: int):
        await db.execute(
            delete(SysCommentLike).where(
                and_(SysCommentLike.comment_id == comment_id, SysCommentLike.user_id == user_id)
            )
        )
        await db.execute(
            update(SysComment).where(
                and_(SysComment.comment_id == comment_id, SysComment.like_count > 0)
            ).values(like_count=SysComment.like_count - 1)
        )
