from __future__ import annotations

from bias_core.extensions import (
    ApiResourceExtender,
    ConditionalExtender,
    EventListenersExtender,
    ForumCapabilitiesExtender,
    LifecycleExtender,
    NotificationsExtender,
    SearchDriverExtender,
)

from bias_ext_subscriptions.backend.forum_contracts import discussion_list_filter_definitions
from bias_ext_subscriptions.backend.frontend import discussion_frontend_extender
from bias_ext_subscriptions.backend.listener_contracts import (
    post_notification_event_listener_definitions,
    post_subscription_event_listener_definitions,
    subscription_event_listener_definitions,
)
from bias_ext_subscriptions.backend.notification_contracts import (
    behavior_user_preference_definitions,
    notification_type_definitions,
    notification_user_preference_definitions,
)
from bias_ext_subscriptions.backend.resource_contracts import (
    discussion_resource_endpoint_definitions,
    discussion_resource_field_definitions,
)
from bias_ext_subscriptions.backend.search_contracts import (
    search_driver_definitions,
    search_filter_definitions,
)


def frontend_extenders():
    return (discussion_frontend_extender(),)


def forum_extenders():
    return (
        ForumCapabilitiesExtender(
            discussion_list_filters=discussion_list_filter_definitions(),
            search_filters=search_filter_definitions(),
        ),
        NotificationsExtender(
            user_preferences=behavior_user_preference_definitions(),
        ),
    )


def search_extenders():
    return (
        SearchDriverExtender(
            drivers=search_driver_definitions(),
        ),
    )


def resource_extenders():
    return (
        ApiResourceExtender("discussion")
        .fields(discussion_resource_field_definitions)
        .endpoints(discussion_resource_endpoint_definitions),
    )


def event_extenders():
    return (
        EventListenersExtender(
            listeners=subscription_event_listener_definitions(),
        ),
    )


def post_integration_extenders():
    return (
        EventListenersExtender(
            listeners=post_subscription_event_listener_definitions(),
        ),
    )


def post_notification_integration_extenders():
    return (
        NotificationsExtender(
            notification_types=notification_type_definitions(),
            user_preferences=notification_user_preference_definitions(),
        ),
        EventListenersExtender(
            listeners=post_notification_event_listener_definitions(),
        ),
    )


def optional_integration_extenders():
    return (
        ConditionalExtender().when_extension_enabled("content", post_integration_extenders),
        ConditionalExtender().when(
            lambda host: _is_extension_enabled(host, "content") and _is_extension_enabled(host, "notifications"),
            post_notification_integration_extenders,
        ),
    )


def lifecycle_extenders():
    return (LifecycleExtender(),)


def _is_extension_enabled(host, extension_id: str) -> bool:
    extension = host.get_runtime_extension(extension_id)
    return bool(extension and extension.runtime.enabled)
