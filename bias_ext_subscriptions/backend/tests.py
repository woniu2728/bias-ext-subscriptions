from django.test import TestCase
from ninja_jwt.tokens import RefreshToken
from unittest.mock import patch

from bias_core.extensions.testing import ExtensionRuntimeTestMixin, build_extension_test_host


def _runtime_facade(name: str):
    from importlib import import_module

    return getattr(import_module("bias_core.extensions.runtime"), name)


def create_runtime_discussion(*args, **kwargs):
    return _runtime_facade("create_runtime_discussion")(*args, **kwargs)


def create_runtime_post(*args, **kwargs):
    return _runtime_facade("create_runtime_post")(*args, **kwargs)


def delete_runtime_post(*args, **kwargs):
    return _runtime_facade("delete_runtime_post")(*args, **kwargs)


def get_runtime_discussion_state_model(*args, **kwargs):
    return _runtime_facade("get_runtime_discussion_state_model")(*args, **kwargs)


def get_runtime_notification_model(*args, **kwargs):
    return _runtime_facade("get_runtime_notification_model")(*args, **kwargs)


def get_runtime_user_model(*args, **kwargs):
    return _runtime_facade("get_runtime_user_model")(*args, **kwargs)


def set_runtime_post_hidden_state(*args, **kwargs):
    return _runtime_facade("set_runtime_post_hidden_state")(*args, **kwargs)


class RuntimeModelProxy:
    def __init__(self, resolver):
        self._resolver = resolver

    def __getattr__(self, name):
        return getattr(self._resolver(), name)


User = RuntimeModelProxy(get_runtime_user_model)


def discussion_state_model():
    return get_runtime_discussion_state_model()


def notification_model():
    return get_runtime_notification_model()


class SubscriptionsExtensionTests(ExtensionRuntimeTestMixin, TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="subscription-author",
            email="subscription-author@example.com",
            password="password123",
            is_email_confirmed=True,
        )
        self.reader = User.objects.create_user(
            username="subscription-reader",
            email="subscription-reader@example.com",
            password="password123",
            is_email_confirmed=True,
        )
        self.admin = User.objects.create_superuser(
            username="subscription-admin",
            email="subscription-admin@example.com",
            password="password123",
        )

    def auth_header(self, user):
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_optional_integrations_are_not_registered_for_base_subscription_runtime(self):
        application = build_extension_test_host("subscriptions")
        listener_names = {
            listener.handler.__name__
            for listener in application.events.get_listeners(extension_id="subscriptions")
        }
        notification_type_codes = {
            item.code
            for item in application.forum_registry.get_notification_types()
            if item.module_id == "subscriptions"
        }
        preference_keys = {
            item.key
            for item in application.forum_registry.get_user_preferences()
            if item.module_id == "subscriptions"
        }

        self.assertIsNone(application.get_service("posts.service"))
        self.assertIsNone(application.get_service("notifications.service"))
        self.assertIn("handle_discussion_created_follow_after_create", listener_names)
        self.assertIn("handle_post_created_follow_after_reply", listener_names)
        self.assertIn("handle_post_approved_follow_after_reply", listener_names)
        self.assertNotIn("handle_post_created_discussion_reply_notification", listener_names)
        self.assertNotIn("discussionReply", notification_type_codes)
        self.assertIn("follow_after_create", preference_keys)
        self.assertIn("follow_after_reply", preference_keys)
        self.assertNotIn("notify_new_post", preference_keys)

    def test_content_post_event_integration_registers_without_notification_integration(self):
        application = build_extension_test_host("content", "subscriptions")
        listener_names = {
            listener.handler.__name__
            for listener in application.events.get_listeners(extension_id="subscriptions")
        }
        notification_type_codes = {
            item.code
            for item in application.forum_registry.get_notification_types()
            if item.module_id == "subscriptions"
        }

        self.assertIsNotNone(application.get_service("content.posts"))
        self.assertIsNone(application.get_service("notifications.service"))
        self.assertIn("handle_post_created_follow_after_reply", listener_names)
        self.assertIn("handle_post_approved_follow_after_reply", listener_names)
        self.assertNotIn("handle_post_created_discussion_reply_notification", listener_names)
        self.assertNotIn("discussionReply", notification_type_codes)

    def test_notification_integration_requires_content_and_notifications(self):
        application = build_extension_test_host("content", "notifications", "subscriptions")
        listener_names = {
            listener.handler.__name__
            for listener in application.events.get_listeners(extension_id="subscriptions")
        }
        notification_type_codes = {
            item.code
            for item in application.forum_registry.get_notification_types()
            if item.module_id == "subscriptions"
        }
        preference_keys = {
            item.key
            for item in application.forum_registry.get_user_preferences()
            if item.module_id == "subscriptions"
        }

        self.assertIsNotNone(application.get_service("content.posts"))
        self.assertIsNotNone(application.get_service("notifications.service"))
        self.assertIn("handle_post_created_discussion_reply_notification", listener_names)
        self.assertIn("handle_post_approved_discussion_reply_notification", listener_names)
        self.assertIn("handle_post_hidden_discussion_reply_notifications", listener_names)
        self.assertIn("handle_post_deleted_discussion_reply_notifications", listener_names)
        self.assertIn("discussionReply", notification_type_codes)
        self.assertIn("notify_new_post", preference_keys)

    def test_extension_detail_api_surfaces_registered_capabilities_for_subscriptions_extension(self):
        response = self.client.get(
            "/api/admin/extensions/subscriptions",
            **self.auth_header(self.admin),
        )

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()["extension"]
        self.assertEqual(payload["frontend_forum_entry"], "extensions/subscriptions/frontend/forum/index.js")
        self.assertTrue(
            any(
                route["path"] == "/following"
                and route["name"] == "following"
                and route["component"] == "extensions/discussions/frontend/forum/DiscussionListView.vue"
                and route["requires_auth"]
                for route in payload["frontend_routes"]
            )
        )
        self.assertTrue(any(item["code"] == "following" for item in payload["discussion_list_filters"]))
        self.assertTrue(any(item["code"] == "is_following" for item in payload["search_filters"]))
        self.assertTrue(any(item["target"] == "discussion" for item in payload["search_drivers"]))
        self.assertTrue(any(item["code"] == "discussionReply" for item in payload["notification_types"]))
        self.assertTrue(any(item["key"] == "follow_after_reply" for item in payload["user_preferences"]))
        self.assertTrue(any(item["key"] == "notify_new_post" for item in payload["user_preferences"]))
        self.assertTrue(
            any(item["module_id"] == "subscriptions" and item["field"] == "is_subscribed" for item in payload["resource_fields"])
        )
        self.assertTrue(
            any(item["module_id"] == "subscriptions" and item["endpoint"] == "subscribe" for item in payload["resource_endpoints"])
        )
        self.assertTrue(
            any(
                item["event"] == "PostCreatedEvent"
                and item["module_id"] == "subscriptions"
                and item.get("source") == "runtime"
                for item in payload["event_listeners"]
            )
        )

    def test_create_discussion_auto_follows_when_preference_enabled(self):
        self.author.preferences = {"follow_after_create": True}
        self.author.save(update_fields=["preferences"])

        with self.captureOnCommitCallbacks(execute=True):
            discussion = create_runtime_discussion(
                title="Auto follow started discussion",
                content="Initial post",
                user=self.author,
            )

        state = discussion_state_model().objects.get(discussion_id=discussion.id, user=self.author)
        self.assertTrue(state.is_subscribed)
        self.assertEqual(state.last_read_post_number, 1)

    def test_reply_auto_follows_when_preference_enabled(self):
        self.author.preferences = {"follow_after_reply": True}
        self.author.save(update_fields=["preferences"])

        discussion = create_runtime_discussion(
            title="Auto follow discussion",
            content="First post",
            user=self.author,
        )
        discussion_state_model().objects.filter(discussion_id=discussion.id, user=self.author).update(
            last_read_post_number=1,
            is_subscribed=False,
        )

        with self.captureOnCommitCallbacks(execute=True):
            reply = create_runtime_post(
                discussion_id=discussion.id,
                content="My followed reply",
                user=self.author,
            )

        state = discussion_state_model().objects.get(discussion_id=discussion.id, user=self.author)
        self.assertEqual(state.last_read_post_number, reply.number)
        self.assertTrue(state.is_subscribed)

    def test_reply_auto_follow_uses_discussion_posts_contract_for_post_number(self):
        self.author.preferences = {"follow_after_reply": True}
        self.author.save(update_fields=["preferences"])

        discussion = create_runtime_discussion(
            title="Auto follow discussion posts contract",
            content="First post",
            user=self.author,
        )
        discussion_state_model().objects.filter(discussion_id=discussion.id, user=self.author).update(
            last_read_post_number=1,
            is_subscribed=False,
        )

        with patch(
            "bias_ext_subscriptions.backend.listeners.get_runtime_post_number",
            side_effect=AssertionError("subscriptions should not use posts.service get_number"),
            create=True,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                reply = create_runtime_post(
                    discussion_id=discussion.id,
                    content="My followed reply through discussion.posts",
                    user=self.author,
                )

        state = discussion_state_model().objects.get(discussion_id=discussion.id, user=self.author)
        self.assertEqual(state.last_read_post_number, reply.number)
        self.assertTrue(state.is_subscribed)

    def test_reply_auto_follow_does_not_move_read_progress_backwards(self):
        self.author.preferences = {"follow_after_reply": True}
        self.author.save(update_fields=["preferences"])

        discussion = create_runtime_discussion(
            title="Auto follow monotonic discussion",
            content="First post",
            user=self.author,
        )
        later_reply = create_runtime_post(
            discussion_id=discussion.id,
            content="Later reply",
            user=self.reader,
        )
        discussion_state_model().objects.filter(discussion_id=discussion.id, user=self.author).update(
            last_read_post_number=later_reply.number,
            is_subscribed=False,
        )

        with self.captureOnCommitCallbacks(execute=True):
            create_runtime_post(
                discussion_id=discussion.id,
                content="Follow should not rewind",
                user=self.author,
            )

        state = discussion_state_model().objects.get(discussion_id=discussion.id, user=self.author)
        self.assertGreaterEqual(state.last_read_post_number, later_reply.number)
        self.assertTrue(state.is_subscribed)

    def test_subscribe_endpoint_creates_state_at_current_last_post(self):
        discussion = create_runtime_discussion(
            title="Explicit subscribe discussion",
            content="First post",
            user=self.author,
        )
        reply = create_runtime_post(
            discussion_id=discussion.id,
            content="Visible reply",
            user=self.author,
        )

        response = self.client.post(
            f"/api/discussions/{discussion.id}/subscribe",
            **self.auth_header(self.reader),
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["is_subscribed"])
        state = discussion_state_model().objects.get(discussion_id=discussion.id, user=self.reader)
        self.assertTrue(state.is_subscribed)
        self.assertEqual(state.last_read_post_number, reply.number)

    def test_subscription_toggle_preserves_existing_read_progress(self):
        discussion = create_runtime_discussion(
            title="Explicit subscribe preserves progress",
            content="First post",
            user=self.author,
        )
        reply = create_runtime_post(
            discussion_id=discussion.id,
            content="Visible reply",
            user=self.author,
        )
        discussion_state_model().objects.update_or_create(
            discussion_id=discussion.id,
            user=self.reader,
            defaults={"is_subscribed": True, "last_read_post_number": reply.number},
        )

        response = self.client.delete(
            f"/api/discussions/{discussion.id}/subscribe",
            **self.auth_header(self.reader),
        )
        self.assertEqual(response.status_code, 200, response.content)
        state = discussion_state_model().objects.get(discussion_id=discussion.id, user=self.reader)
        self.assertFalse(state.is_subscribed)
        self.assertEqual(state.last_read_post_number, reply.number)

        response = self.client.post(
            f"/api/discussions/{discussion.id}/subscribe",
            **self.auth_header(self.reader),
        )
        self.assertEqual(response.status_code, 200, response.content)
        state.refresh_from_db()
        self.assertTrue(state.is_subscribed)
        self.assertEqual(state.last_read_post_number, reply.number)

    def test_discussion_list_following_filter_uses_registered_filter_code(self):
        followed = create_runtime_discussion(
            title="关注过滤 API",
            content="关注过滤内容",
            user=self.author,
        )
        other = create_runtime_discussion(
            title="未关注过滤 API",
            content="未关注过滤内容",
            user=self.author,
        )
        discussion_state_model().objects.update_or_create(
            discussion_id=followed.id,
            user=self.reader,
            defaults={"is_subscribed": True, "last_read_post_number": 1},
        )
        discussion_state_model().objects.update_or_create(
            discussion_id=other.id,
            user=self.reader,
            defaults={"is_subscribed": False, "last_read_post_number": 1},
        )

        following_response = self.client.get(
            "/api/discussions/",
            {"filter": "following"},
            **self.auth_header(self.reader),
        )
        self.assertEqual(following_response.status_code, 200, following_response.content)
        self.assertEqual([item["id"] for item in following_response.json()["data"]], [followed.id])

    def test_discussion_list_exposes_following_filter_route(self):
        create_runtime_discussion(
            title="关注过滤器元数据",
            content="用于验证扩展过滤器",
            user=self.author,
        )

        response = self.client.get(
            "/api/discussions/",
            {"page": 0, "limit": 999},
            **self.auth_header(self.reader),
        )

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertTrue(any(item["code"] == "following" and item["route_path"] == "/following" for item in payload["available_filters"]))
        self.assertTrue(any(item["code"] == "following" and item["requires_authenticated_user"] for item in payload["available_filters"]))

    def test_search_api_supports_registered_following_filter(self):
        followed = create_runtime_discussion(
            title="关注搜索命中讨论",
            content="关注搜索过滤关键字",
            user=self.author,
        )
        other = create_runtime_discussion(
            title="关注搜索未命中讨论",
            content="关注搜索过滤关键字",
            user=self.author,
        )
        discussion_state_model().objects.update_or_create(
            discussion_id=followed.id,
            user=self.reader,
            defaults={"is_subscribed": True, "last_read_post_number": 1},
        )
        discussion_state_model().objects.update_or_create(
            discussion_id=other.id,
            user=self.reader,
            defaults={"is_subscribed": False, "last_read_post_number": 1},
        )

        response = self.client.get(
            "/api/search",
            {"q": "关注搜索过滤关键字 is:following", "type": "discussions"},
            **self.auth_header(self.reader),
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([item["id"] for item in response.json()["discussions"]], [followed.id])

    def test_search_filters_api_exposes_registered_following_filter_syntax(self):
        response = self.client.get("/api/search/filters", {"target": "discussions"})

        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("is:following", {item["syntax"] for item in response.json()["filters"]})

    def test_delete_post_cleans_discussion_reply_notifications(self):
        discussion = create_runtime_discussion(
            title="Notification cleanup discussion",
            content="First post",
            user=self.author,
        )
        reply = create_runtime_post(
            discussion_id=discussion.id,
            content="带通知的回复",
            user=self.reader,
        )
        notification = notification_model().objects.create(
            user=self.author,
            from_user=self.reader,
            type="discussionReply",
            subject_type="discussion",
            subject_id=discussion.id,
            data={
                "discussion_id": discussion.id,
                "post_id": reply.id,
                "post_number": reply.number,
            },
        )

        with self.captureOnCommitCallbacks(execute=True):
            delete_runtime_post(reply.id, self.reader)

        notification.refresh_from_db()
        self.assertTrue(notification.is_deleted)

    def test_hiding_post_cleans_discussion_reply_notifications(self):
        discussion = create_runtime_discussion(
            title="Hidden notification cleanup discussion",
            content="First post",
            user=self.author,
        )
        post = create_runtime_post(
            discussion_id=discussion.id,
            content="会被隐藏的回复",
            user=self.author,
        )
        notification = notification_model().objects.create(
            user=self.reader,
            from_user=self.author,
            type="discussionReply",
            subject_type="discussion",
            subject_id=discussion.id,
            data={
                "discussion_id": discussion.id,
                "post_id": post.id,
                "post_number": post.number,
            },
        )

        with self.captureOnCommitCallbacks(execute=True):
            set_runtime_post_hidden_state(post, self.admin, True)

        notification.refresh_from_db()
        self.assertTrue(notification.is_deleted)



