"""评论 VO 模型单元测试"""
import pytest
from pydantic import ValidationError

from module_comment.entity.vo.comment_vo import (
    CommentCreateVO, CommentUpdateVO, CommentQueryVO,
    CommentAuditVO, CommentAdminQueryVO, CommentItemVO, CommentUserVO,
)


class TestCommentCreateVO:

    def test_valid_create(self):
        vo = CommentCreateVO(biz_type='article', biz_id='123', content='好文章')
        assert vo.biz_type == 'article'
        assert vo.biz_id == '123'
        assert vo.content == '好文章'
        assert vo.parent_id is None

    def test_create_with_reply(self):
        vo = CommentCreateVO(
            biz_type='article', biz_id='123', content='同意',
            parent_id=1, root_id=1, reply_user_id=2,
        )
        assert vo.parent_id == 1
        assert vo.root_id == 1
        assert vo.reply_user_id == 2

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_type='article', biz_id='123', content='')

    def test_content_too_long(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_type='article', biz_id='123', content='a' * 1001)

    def test_missing_biz_type(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_id='123', content='hello')

    def test_missing_biz_id(self):
        with pytest.raises(ValidationError):
            CommentCreateVO(biz_type='article', content='hello')

    def test_content_max_boundary(self):
        vo = CommentCreateVO(biz_type='article', biz_id='1', content='a' * 1000)
        assert len(vo.content) == 1000


class TestCommentUpdateVO:

    def test_valid_update(self):
        vo = CommentUpdateVO(content='修改内容')
        assert vo.content == '修改内容'

    def test_empty_content(self):
        with pytest.raises(ValidationError):
            CommentUpdateVO(content='')

    def test_too_long(self):
        with pytest.raises(ValidationError):
            CommentUpdateVO(content='x' * 1001)


class TestCommentQueryVO:

    def test_defaults(self):
        vo = CommentQueryVO()
        assert vo.page == 1
        assert vo.page_size == 20
        assert vo.sort == 'latest'

    def test_hottest_sort(self):
        vo = CommentQueryVO(sort='hottest')
        assert vo.sort == 'hottest'

    def test_invalid_sort(self):
        with pytest.raises(ValidationError):
            CommentQueryVO(sort='random')

    def test_page_zero(self):
        with pytest.raises(ValidationError):
            CommentQueryVO(page=0)

    def test_page_size_too_large(self):
        with pytest.raises(ValidationError):
            CommentQueryVO(page_size=51)


class TestCommentAuditVO:

    def test_valid_audit(self):
        vo = CommentAuditVO(comment_ids=[1, 2, 3], status=1)
        assert len(vo.comment_ids) == 3
        assert vo.status == 1

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            CommentAuditVO(comment_ids=[], status=1)

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            CommentAuditVO(comment_ids=[1], status=5)

    def test_with_remark(self):
        vo = CommentAuditVO(comment_ids=[1], status=0, remark='违规内容')
        assert vo.remark == '违规内容'


class TestCommentItemVO:

    def test_build_item(self):
        item = CommentItemVO(
            comment_id=1,
            user=CommentUserVO(user_id=1, nick_name='张三', avatar=''),
            content='测试评论',
            like_count=10,
        )
        assert item.comment_id == 1
        assert item.user.nick_name == '张三'
        assert item.is_liked is False
        assert item.replies == []
        assert item.has_more_replies is False

    def test_with_replies(self):
        reply = CommentItemVO(
            comment_id=2,
            user=CommentUserVO(user_id=2, nick_name='李四'),
            reply_user=CommentUserVO(user_id=1, nick_name='张三'),
            content='回复内容',
        )
        item = CommentItemVO(
            comment_id=1,
            user=CommentUserVO(user_id=1, nick_name='张三'),
            content='根评论',
            replies=[reply],
            has_more_replies=True,
        )
        assert len(item.replies) == 1
        assert item.replies[0].reply_user.nick_name == '张三'
        assert item.has_more_replies is True
