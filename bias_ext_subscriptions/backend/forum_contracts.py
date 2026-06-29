from __future__ import annotations

from bias_core.extensions import DiscussionListFilterDefinition

from bias_ext_subscriptions.backend.constants import EXTENSION_ID
from bias_ext_subscriptions.backend.search import apply_following_discussion_list_filter


def discussion_list_filter_definitions():
    return (
        DiscussionListFilterDefinition(
            code="following",
            label="关注中",
            module_id=EXTENSION_ID,
            applier=apply_following_discussion_list_filter,
            description="仅显示当前用户已关注的讨论。",
            icon="fas fa-bell",
            requires_authenticated_user=True,
            order=20,
            route_path="/following",
        ),
    )
