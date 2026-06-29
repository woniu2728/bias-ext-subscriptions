from __future__ import annotations

from bias_core.extensions import NotificationTypeDefinition, UserPreferenceDefinition

from bias_ext_subscriptions.backend.constants import EXTENSION_ID


def behavior_user_preference_definitions():
    return (
        UserPreferenceDefinition(
            key="follow_after_reply",
            label="回复后自动关注",
            module_id=EXTENSION_ID,
            description="参与讨论后自动把该讨论加入关注列表。",
            category="behavior",
            default_value=False,
        ),
        UserPreferenceDefinition(
            key="follow_after_create",
            label="发起讨论后自动关注",
            module_id=EXTENSION_ID,
            description="你创建的新讨论默认加入关注列表。",
            category="behavior",
            default_value=False,
        ),
    )


def notification_type_definitions():
    return (
        NotificationTypeDefinition(
            code="discussionReply",
            label="讨论新回复",
            module_id=EXTENSION_ID,
            description="通知讨论作者和关注者有新回复。",
            icon="fas fa-reply",
            navigation_scope="post",
            preference_key="notify_new_post",
            preference_label="关注讨论有新回复时通知我",
            preference_description="关闭后仍保留关注状态，但不再接收关注讨论的新回复通知。",
        ),
    )


def notification_user_preference_definitions():
    return (
        UserPreferenceDefinition(
            key="notify_new_post",
            label="关注讨论有新回复时通知我",
            module_id=EXTENSION_ID,
            description="关闭后仍保留关注状态，但不再接收关注讨论的新回复通知。",
            category="notification",
            default_value=True,
        ),
    )
