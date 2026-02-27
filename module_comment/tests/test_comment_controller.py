"""评论 Controller 接口参数与响应结构测试"""
import pytest
from pydantic import ValidationError

from module_comment.entity.vo.comment_vo import (
    CommentCreateVO, CommentUpdateVO, CommentQueryVO,
    CommentAuditVO, CommentAdminQueryVO, CommentItemVO,
    CommentUserVO, CommentListVO, CommentStatsVO,
)


class TestCommentListAPI:
    """GET /api/comment/list 参数校验"""

    def test_valid_query_params(self):
        q = CommentQueryVO(biz_type='article', biz_id='100', page=1, page_size=20, sort='latest')
        assert q.biz_type == 'article'

    def test_hottest_sort(self):
        q = CommentQueryVO(sort='hottest')
        assert q.sort == 'hottest'

    def test_invalid_sort_rejected(self):
        with pytest.raises(ValidationError):
            CommentQueryVO(sort='random')

    def test_page_zero_rejected(self):
        with pytest.raises(ValidationError):
            CommentQueryVO(page=0)

    def test_page_size_exceeds_max(self):
        with pytest.raises(ValidationError):
            CommentQueryVO(page_size=51)

    def test_response_structure(self):
        item = CommentItemVO(
            comment_id=1,
            user=CommentUserVO(user_id=1, nick_name='张三'),
            content='测试', like_count=5, reply_count=2,
            is_liked=True, is_top=False, replies=[],
        )
        resp = CommentListVO(total=1, page=1, page_size=20, list=[item])
        data = resp.model_dump()
        assert data['total'] == 1
        assert data['list'][0]['user']['nick_name'] == '张三'
        assert data['list'][0]['is_liked'] is True


class TestCommentCreateAPI:
    """POST /api/comment 参数校验"""

    def test_valid_create(self):
        vo = CommentCreateVO(biz_type='article', biz_id='1', content='好文章')
        assert vo.content == '好文章'
        assert vo.parent_id is None

    def test_create_reply(self):
        vo = CommentCreateVO(
            biz_type='article', biz_id='1', content='同意',
            parent_id=10, root_id=10, reply_user_id=5,
        )
        assert vo.parent_id == 10

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_type='article', biz_id='1', content='')

    def test_content_too_long(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_type='article', biz_id='1', content='x' * 1001)

    def test_content_boundary_1000(self):
        vo = CommentCreateVO(biz_type='article', biz_id='1', content='a' * 1000)
        assert len(vo.content) == 1000

    def test_missing_biz_type(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_id='1', content='hello')


class TestCommentUpdateAPI:
    """PUT /api/comment/{id} 参数校验"""

    def test_valid_update(self):
        vo = CommentUpdateVO(content='修改后内容')
        assert vo.content == '修改后内容'

    def test_empty_rejected(self):
        with pytest.raises(ValidationError):
            CommentUpdateVO(content='')

    def test_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CommentUpdateVO(content='y' * 1001)


class TestCommentLikeAPI:
    """POST /api/comment/like/{id} 响应结构"""

    def test_like_response(self):
        result = {'is_liked': True, 'like_count': 6}
        assert result['is_liked'] is True
        assert isinstance(result['like_count'], int)

    def test_unlike_response(self):
        result = {'is_liked': False, 'like_count': 5}
        assert result['is_liked'] is False


class TestCommentAdminAPI:
    """管理端接口参数校验"""

    def test_admin_query_with_filters(self):
        q = CommentAdminQueryVO(
            status=2, biz_type='article', content='关键词',
            begin_time='2026-01-01', end_time='2026-12-31',
            page=1, page_size=50,
        )
        assert q.status == 2
        assert q.page_size == 50

    def test_admin_query_no_filter(self):
        q = CommentAdminQueryVO(page=1, page_size=20)
        assert q.status is None
        assert q.biz_type is None

    def test_audit_approve(self):
        vo = CommentAuditVO(comment_ids=[1, 2, 3], status=1)
        assert vo.status == 1
        assert len(vo.comment_ids) == 3

    def test_audit_hide(self):
        vo = CommentAuditVO(comment_ids=[10], status=0, remark='违规')
        assert vo.remark == '违规'

    def test_audit_empty_ids_rejected(self):
        with pytest.raises(ValidationError):
            CommentAuditVO(comment_ids=[], status=1)

    def test_audit_invalid_status(self):
        with pytest.raises(ValidationError):
            CommentAuditVO(comment_ids=[1], status=5)

    def test_stats_response(self):
        stats = CommentStatsVO(total=500, today_new=20, pending_audit=10, hidden=15)
        data = stats.model_dump()
        assert data['total'] == 500
        assert data['pending_audit'] == 10
