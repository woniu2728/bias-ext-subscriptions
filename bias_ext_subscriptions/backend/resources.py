from __future__ import annotations

from bias_core.extensions.runtime import get_runtime_discussion_subscription_state


def resolve_discussion_subscription_state(discussion, context: dict) -> bool:
    if hasattr(discussion, "is_subscribed"):
        return bool(getattr(discussion, "is_subscribed"))

    user = context.get("user")
    return get_runtime_discussion_subscription_state(discussion, user)


