from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.router import APIRouterPro
from config.get_db import get_db
from module_comment.entity.vo.comment_vo import CommentCreateVO, CommentUpdateVO
from module_comment.service.comment_service import CommentService

commentRouter = APIRouterPro(prefix='/api/comment', tags=['评论-H5端'])


@commentRouter.get('/list')
async def get_comment_list(
    biz_type: str = Query(...),
    biz_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    sort: str = Query('latest'),
    db: AsyncSession = Depends(get_db),
):
    result = await CommentService.get_list(db, biz_type, biz_id, page, page_size, sort)
    return {'code': 200, 'msg': 'success', 'data': result.model_dump()}


@commentRouter.get('/replies/{root_id}')
async def get_replies(
    root_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    from module_comment.dao.comment_dao import CommentDao
    total, rows = await CommentDao.get_replies(db, root_id, page, page_size)
    return {'code': 200, 'msg': 'success', 'data': {'total': total, 'list': [
        {'comment_id': r.comment_id, 'content': r.content, 'create_time': str(r.create_time)}
        for r in rows
    ]}}


@commentRouter.get('/count')
async def get_count(
    biz_type: str = Query(...),
    biz_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    count = await CommentService.count(db, biz_type, biz_id)
    return {'code': 200, 'msg': 'success', 'data': count}


@commentRouter.post('')
async def create_comment(
    req: CommentCreateVO,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        comment = await CommentService.create(
            db, req, user_id=1, user_name='test',
            ip=request.client.host if request.client else '',
        )
        return {'code': 200, 'msg': '评论发布成功', 'data': {
            'comment_id': comment.comment_id,
            'content': comment.content,
        }}
    except ValueError as e:
        return {'code': 400, 'msg': str(e)}


@commentRouter.put('/{comment_id}')
async def update_comment(
    comment_id: int,
    req: CommentUpdateVO,
    db: AsyncSession = Depends(get_db),
):
    try:
        await CommentService.update(db, comment_id, req.content, user_id=1)
        return {'code': 200, 'msg': '修改成功'}
    except (ValueError, PermissionError) as e:
        return {'code': 400, 'msg': str(e)}


@commentRouter.delete('/{comment_id}')
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        await CommentService.delete(db, comment_id, user_id=1)
        return {'code': 200, 'msg': '删除成功'}
    except (ValueError, PermissionError) as e:
        return {'code': 400, 'msg': str(e)}


@commentRouter.post('/like/{comment_id}')
async def toggle_like(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await CommentService.toggle_like(db, comment_id, user_id=1)
        return {'code': 200, 'msg': '操作成功', 'data': result}
    except ValueError as e:
        return {'code': 400, 'msg': str(e)}
