from __future__ import annotations

from bias_core.extensions import (
    ExtensionSearchDriverDefinition,
    SearchFilterDefinition,
)

from bias_ext_subscriptions.backend.constants import EXTENSION_ID
from bias_ext_subscriptions.backend.search import (
    apply_discussion_following_search_filter,
    parse_following_search_filter,
)


def search_filter_definitions():
    return (
        SearchFilterDefinition(
            code="is_following",
            label="仅关注讨论",
            module_id=EXTENSION_ID,
            target="discussion",
            parser=parse_following_search_filter,
            applier=apply_discussion_following_search_filter,
            syntax="is:following",
            description="仅返回当前用户已关注的讨论。",
        ),
    )


def search_driver_definitions():
    return (
        ExtensionSearchDriverDefinition(
            target="discussion",
            driver="database",
            filters=search_filter_definitions(),
            description="按关注状态过滤讨论搜索。",
        ),
    )
