from __future__ import annotations

from bias_core.extensions import ResourceEndpointDefinition, ResourceFieldDefinition

from bias_ext_subscriptions.backend.constants import EXTENSION_ID
from bias_ext_subscriptions.backend.handlers import (
    dispatch_discussion_subscribe,
    dispatch_discussion_unsubscribe,
)
from bias_ext_subscriptions.backend.resources import resolve_discussion_subscription_state


def discussion_resource_field_definitions():
    return (
        ResourceFieldDefinition(
            resource="discussion",
            field="is_subscribed",
            module_id=EXTENSION_ID,
            resolver=resolve_discussion_subscription_state,
            description="当前用户是否关注该讨论。",
        ),
    )


def discussion_resource_endpoint_definitions():
    return (
        ResourceEndpointDefinition(
            resource="discussion",
            endpoint="subscribe",
            module_id=EXTENSION_ID,
            handler=dispatch_discussion_subscribe,
            methods=("POST",),
            path="discussions/{object_id}/subscribe",
            absolute_path=True,
            auth_required=True,
        ),
        ResourceEndpointDefinition(
            resource="discussion",
            endpoint="unsubscribe",
            module_id=EXTENSION_ID,
            handler=dispatch_discussion_unsubscribe,
            methods=("DELETE",),
            path="discussions/{object_id}/subscribe",
            absolute_path=True,
            auth_required=True,
        ),
    )
