from __future__ import annotations


def get_content_discussion_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("content.discussions")


def resolve_discussion_subscription_state(discussion, context: dict) -> bool:
    if hasattr(discussion, "is_subscribed"):
        return bool(getattr(discussion, "is_subscribed"))

    user = context.get("user")
    return _service_method(get_content_discussion_service(), "is_subscribed")(discussion, user)


def _service_method(service, name: str):
    if isinstance(service, dict):
        method = service.get(name)
    else:
        method = getattr(service, name, None)
    if not callable(method):
        raise RuntimeError(f"Subscriptions 扩展运行时服务缺少方法: {name}")
    return method


