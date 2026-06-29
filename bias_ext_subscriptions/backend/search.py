from __future__ import annotations

from bias_core.extensions.runtime import get_runtime_discussion_state_model


def parse_following_search_filter(token: str) -> bool | None:
    if not token or ":" not in token:
        return None

    prefix, value = token.split(":", 1)
    if prefix.lower() != "is":
        return None

    return True if value.strip().lower() == "following" else None


def apply_discussion_following_search_filter(queryset, enabled: bool, context: dict):
    user = context.get("user")
    if not enabled:
        return queryset
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    return _filter_following_discussions(queryset, user)


def apply_following_discussion_list_filter(queryset, context: dict):
    user = context.get("user")
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    return _filter_following_discussions(queryset, user)


def _filter_following_discussions(queryset, user):
    DiscussionUser = get_runtime_discussion_state_model()
    return queryset.filter(
        pk__in=DiscussionUser.objects.filter(
            user=user,
            is_subscribed=True,
        ).values("discussion_id")
    )

