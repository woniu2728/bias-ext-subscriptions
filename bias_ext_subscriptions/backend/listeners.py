def get_content_discussion_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("content.discussions")


def get_content_post_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("content.posts")


def get_user_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("users.service")


def get_notification_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("notifications.service")


def handle_post_created_discussion_reply_notification(event) -> None:
    if not event.is_approved:
        return

    _notify_discussion_reply(
        discussion_id=event.discussion_id,
        post_id=event.post_id,
        actor_user_id=event.actor_user_id,
    )


def handle_post_approved_discussion_reply_notification(event) -> None:
    if not event.actor_user_id:
        return

    _notify_discussion_reply(
        discussion_id=event.discussion_id,
        post_id=event.post_id,
        actor_user_id=event.actor_user_id,
    )


def handle_discussion_created_follow_after_create(event) -> None:
    _follow_discussion_if_enabled(
        discussion_id=event.discussion_id,
        user_id=event.actor_user_id,
        preference_key="follow_after_create",
        last_read_post_number=1,
    )


def handle_post_created_follow_after_reply(event) -> None:
    if not event.is_approved:
        return

    _follow_discussion_if_enabled(
        discussion_id=event.discussion_id,
        user_id=event.actor_user_id,
        preference_key="follow_after_reply",
        post_id=event.post_id,
    )


def handle_post_approved_follow_after_reply(event) -> None:
    if not event.actor_user_id:
        return

    _follow_discussion_if_enabled(
        discussion_id=event.discussion_id,
        user_id=event.actor_user_id,
        preference_key="follow_after_reply",
        post_id=event.post_id,
    )


def handle_post_hidden_discussion_reply_notifications(event) -> None:
    if event.is_hidden:
        _delete_discussion_reply_notifications_for_post(event.post_id)


def handle_post_deleted_discussion_reply_notifications(event) -> None:
    _delete_discussion_reply_notifications_for_post(event.post_id)


def _notify_discussion_reply(*, discussion_id: int, post_id: int, actor_user_id: int) -> None:
    from_user = _resolve_user_or_none(actor_user_id)
    if from_user is None:
        return

    notification_service = get_notification_service()
    if notification_service is None:
        return
    notify_discussion_reply = _service_method(notification_service, "notify_discussion_reply")
    if notify_discussion_reply is None:
        return
    notify_discussion_reply(discussion_id=discussion_id, post_id=post_id, from_user=from_user)


def _follow_discussion_if_enabled(
    *,
    discussion_id: int,
    user_id: int,
    preference_key: str,
    post_id: int | None = None,
    last_read_post_number: int | None = None,
) -> None:
    user = _resolve_user_or_none(user_id)
    if user is None or not _get_user_preference(user, preference_key, fallback=False):
        return

    if last_read_post_number is None and post_id is not None:
        last_read_post_number = _service_method(get_content_post_service(), "get_post_number")(post_id)

    _service_method(get_content_discussion_service(), "follow_if_enabled")(
        discussion_id=discussion_id,
        user_id=user_id,
        last_read_post_number=last_read_post_number,
    )


def _resolve_user_or_none(user_id: int):
    try:
        return _service_method(get_user_service(), "get_by_id")(user_id)
    except Exception:
        return None


def _get_user_preference(user, key: str, *, fallback=False):
    get_preference = _service_method(get_user_service(), "get_preference")
    try:
        return get_preference(user, key, fallback=fallback)
    except TypeError:
        value = get_preference(user, key)
        return fallback if value is None else value


def _delete_discussion_reply_notifications_for_post(post_id: int) -> None:
    notification_service = get_notification_service()
    if notification_service is None:
        return
    delete_for_post = _service_method(notification_service, "delete_discussion_reply_for_post")
    if delete_for_post is not None:
        delete_for_post(post_id)


def _service_method(service, name: str):
    if isinstance(service, dict):
        method = service.get(name)
    else:
        method = getattr(service, name, None)
    return method if callable(method) else None

