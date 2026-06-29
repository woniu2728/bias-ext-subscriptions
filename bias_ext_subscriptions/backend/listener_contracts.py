from __future__ import annotations

from bias_core.extensions import ExtensionEventListenerDefinition

from bias_ext_subscriptions.backend.listeners import (
    handle_discussion_created_follow_after_create,
    handle_post_approved_discussion_reply_notification,
    handle_post_approved_follow_after_reply,
    handle_post_created_discussion_reply_notification,
    handle_post_created_follow_after_reply,
    handle_post_deleted_discussion_reply_notifications,
    handle_post_hidden_discussion_reply_notifications,
)


def subscription_event_listener_definitions():
    return (
        ExtensionEventListenerDefinition(
            event_type="discussions.discussion.created",
            handler=handle_discussion_created_follow_after_create,
            description="讨论创建后按用户偏好自动关注新讨论。",
        ),
    )


def post_subscription_event_listener_definitions():
    return (
        ExtensionEventListenerDefinition(
            event_type="posts.post.created",
            handler=handle_post_created_follow_after_reply,
            description="已发布回复后按用户偏好自动关注参与的讨论。",
        ),
        ExtensionEventListenerDefinition(
            event_type="posts.post.approved",
            handler=handle_post_approved_follow_after_reply,
            description="回复审核通过后按用户偏好自动关注参与的讨论。",
        ),
    )


def post_notification_event_listener_definitions():
    return (
        ExtensionEventListenerDefinition(
            event_type="posts.post.created",
            handler=handle_post_created_discussion_reply_notification,
            description="已发布回复后为讨论作者和关注者派发讨论回复通知。",
        ),
        ExtensionEventListenerDefinition(
            event_type="posts.post.approved",
            handler=handle_post_approved_discussion_reply_notification,
            description="回复审核通过后为讨论作者和关注者派发讨论回复通知。",
        ),
        ExtensionEventListenerDefinition(
            event_type="posts.post.hidden",
            handler=handle_post_hidden_discussion_reply_notifications,
            description="回复隐藏后清理该回复产生的关注讨论通知。",
        ),
        ExtensionEventListenerDefinition(
            event_type="posts.post.deleted",
            handler=handle_post_deleted_discussion_reply_notifications,
            description="回复删除后清理该回复产生的关注讨论通知。",
        ),
    )
