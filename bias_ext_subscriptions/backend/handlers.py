from __future__ import annotations

from django.core.exceptions import PermissionDenied

from bias_core.extensions.platform import api_error


def get_content_discussion_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("content.discussions")


def get_user_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("users.service")


def ensure_user_not_suspended(user, action: str) -> None:
    _service_method(get_user_service(), "ensure_not_suspended")(user, action)


def set_discussion_subscription_state(discussion_id: int, user, subscribed: bool):
    return _service_method(get_content_discussion_service(), "set_subscription")(
        discussion_id,
        user,
        subscribed,
    )


def is_discussion_not_found(exc: Exception) -> bool:
    from django.http import Http404

    return isinstance(exc, Http404)


def dispatch_discussion_subscribe(context):
    discussion_id = _discussion_object_id(context)
    try:
        ensure_user_not_suspended(context["user"], "关注讨论")
        set_discussion_subscription_state(discussion_id, context["user"], True)
        return {"message": "已关注讨论", "is_subscribed": True}
    except PermissionDenied as e:
        return api_error(str(e), status=403)
    except Exception as e:
        if is_discussion_not_found(e):
            return api_error("讨论不存在", status=404)
        raise


def dispatch_discussion_unsubscribe(context):
    discussion_id = _discussion_object_id(context)
    try:
        ensure_user_not_suspended(context["user"], "关注讨论")
        set_discussion_subscription_state(discussion_id, context["user"], False)
        return {"message": "已取消关注", "is_subscribed": False}
    except PermissionDenied as e:
        return api_error(str(e), status=403)
    except Exception as e:
        if is_discussion_not_found(e):
            return api_error("讨论不存在", status=404)
        raise


def _discussion_object_id(context) -> int:
    try:
        return int(context.get("object_id") or 0)
    except (TypeError, ValueError):
        return 0


def _service_method(service, name: str):
    if isinstance(service, dict):
        method = service.get(name)
    else:
        method = getattr(service, name, None)
    if not callable(method):
        raise RuntimeError(f"Subscriptions 扩展运行时服务缺少方法: {name}")
    return method

