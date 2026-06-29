from __future__ import annotations

from django.core.exceptions import PermissionDenied

from bias_core.extensions.platform import api_error


def ensure_runtime_user_not_suspended(*args, **kwargs):
    from bias_core.extensions.runtime import ensure_runtime_user_not_suspended as runtime_ensure_user_not_suspended

    return runtime_ensure_user_not_suspended(*args, **kwargs)


def is_runtime_discussion_not_found(*args, **kwargs):
    from bias_core.extensions.runtime import is_runtime_discussion_not_found as runtime_is_discussion_not_found

    return runtime_is_discussion_not_found(*args, **kwargs)


def set_runtime_discussion_subscription_state(*args, **kwargs):
    from bias_core.extensions.runtime import (
        set_runtime_discussion_subscription_state as runtime_set_discussion_subscription_state,
    )

    return runtime_set_discussion_subscription_state(*args, **kwargs)


def dispatch_discussion_subscribe(context):
    discussion_id = _discussion_object_id(context)
    try:
        ensure_runtime_user_not_suspended(context["user"], "关注讨论")
        set_runtime_discussion_subscription_state(discussion_id, context["user"], True)
        return {"message": "已关注讨论", "is_subscribed": True}
    except PermissionDenied as e:
        return api_error(str(e), status=403)
    except Exception as e:
        if is_runtime_discussion_not_found(e):
            return api_error("讨论不存在", status=404)
        raise


def dispatch_discussion_unsubscribe(context):
    discussion_id = _discussion_object_id(context)
    try:
        ensure_runtime_user_not_suspended(context["user"], "关注讨论")
        set_runtime_discussion_subscription_state(discussion_id, context["user"], False)
        return {"message": "已取消关注", "is_subscribed": False}
    except PermissionDenied as e:
        return api_error(str(e), status=403)
    except Exception as e:
        if is_runtime_discussion_not_found(e):
            return api_error("讨论不存在", status=404)
        raise


def _discussion_object_id(context) -> int:
    try:
        return int(context.get("object_id") or 0)
    except (TypeError, ValueError):
        return 0

