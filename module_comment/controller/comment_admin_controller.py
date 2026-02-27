from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.router import APIRouterPro
from config.get_db import get_db
from module_comment.entity.vo.comment_vo import CommentAuditVO, CommentAdminQueryVO, CommentUpdateVO
from module_comment.service.comment_service import CommentService

commentAdminRouter = APIRouterPro(prefix='/api/admin/comment', tags=['评论-管理端'])


@commentAdminRouter.get('/list')
async def admin_list(
    status: int = Query(None),
    biz_type: str = Query(None),
    content: str = Query(None),
    begin_time: str = Query(None),
    end_time: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = CommentAdminQueryVO(
        status=status, biz_type=biz_type, content=content,
        begin_time=begin_time, end_time=end_time, page=page, page_size=page_size,
    )
    result = await CommentService.admin_list(db, query)
    return {'code': 200, 'msg': 'success', 'data': result.model_dump()}


@commentAdminRouter.put('/audit')
async def audit_comment(
    req: CommentAuditVO,
    db: AsyncSession = Depends(get_db),
):
    await CommentService.admin_audit(db, req)
    return {'code': 200, 'msg': '审核成功'}


@commentAdminRouter.put('/{comment_id}')
async def admin_update(
    comment_id: int,
    req: CommentUpdateVO,
    db: AsyncSession = Depends(get_db),
):
    from module_comment.dao.comment_dao import CommentDao
    await CommentDao.update_content(db, comment_id, req.content, update_by='admin')
    await db.commit()
    return {'code': 200, 'msg': '修改成功'}


@commentAdminRouter.delete('/{comment_id}')
async def admin_delete(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    await CommentService.admin_delete(db, comment_id)
    return {'code': 200, 'msg': '删除成功'}


@commentAdminRouter.get('/stats')
async def get_stats(db: AsyncSession = Depends(get_db)):
    stats = await CommentService.get_stats(db)
    return {'code': 200, 'msg': 'success', 'data': stats.model_dump()}
