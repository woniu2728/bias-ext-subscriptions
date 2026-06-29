from __future__ import annotations

from bias_core.extensions import FrontendExtender


def frontend_extender():
    return (
        FrontendExtender(
            forum_entry="extensions/subscriptions/frontend/forum/index.js",
        )
        .route(
            "/following",
            "following",
            "extensions/discussions/frontend/forum/DiscussionListView.vue",
            title="关注的讨论",
            description="查看你关注的讨论和最新回复。",
            order=20,
            requires_auth=True,
        )
    )
