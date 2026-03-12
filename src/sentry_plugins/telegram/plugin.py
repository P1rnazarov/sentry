from sentry.integrations.base import FeatureDescription, IntegrationFeatures
from sentry.plugins.base.structs import Notification
from sentry.plugins.bases.notify import NotificationPlugin
from sentry_plugins.base import CorePluginMixin
from sentry_plugins.utils import get_secret_field_config

from .client import TelegramClient

DESCRIPTION = """
Get notified of Sentry alerts in Telegram via a bot.

Send real-time error and performance notifications directly to a Telegram chat or group.
"""


class TelegramPlugin(CorePluginMixin, NotificationPlugin):
    description = DESCRIPTION
    slug = "telegram"
    title = "Telegram"
    conf_title = "Telegram"
    conf_key = "telegram"
    required_field = "bot_token"
    feature_descriptions = [
        FeatureDescription(
            """
            Receive Telegram notifications for Sentry alerts.
            """,
            IntegrationFeatures.ALERT_RULE,
        ),
    ]

    def is_configured(self, project) -> bool:
        return all(self.get_option(key, project) for key in ("bot_token", "chat_id"))

    def get_config(self, project, user=None, initial=None, add_additional_fields: bool = False):
        bot_token = self.get_option("bot_token", project)
        chat_id = self.get_option("chat_id", project)

        bot_token_field = get_secret_field_config(
            bot_token,
            "Bot token from @BotFather.",
            include_prefix=True,
        )
        bot_token_field.update({"name": "bot_token", "label": "Bot Token"})

        return [
            bot_token_field,
            {
                "name": "chat_id",
                "label": "Chat ID",
                "type": "text",
                "required": True,
                "default": chat_id or "",
                "help": "Chat ID or group ID to send notifications to. Use @userinfobot to find your ID.",
            },
            {
                "name": "topic_id",
                "label": "Topic ID (optional)",
                "type": "text",
                "required": False,
                "default": self.get_option("topic_id", project) or "",
                "help": "Thread/Topic ID for Forum supergroups. Leave empty to send to General.",
            },
            # --- Message Constructor ---
            {
                "name": "show_level",
                "label": "Show Level",
                "type": "bool",
                "required": False,
                "default": self.get_option("show_level", project) or True,
                "help": "Show event level (error, warning, info...).",
            },
            {
                "name": "show_culprit",
                "label": "Show Culprit",
                "type": "bool",
                "required": False,
                "default": self.get_option("show_culprit", project) or True,
                "help": "Show the source of the error.",
            },
            {
                "name": "show_message",
                "label": "Show Message",
                "type": "bool",
                "required": False,
                "default": self.get_option("show_message", project) or False,
                "help": "Show the error message text.",
            },
            {
                "name": "included_tags",
                "label": "Tags",
                "type": "text",
                "required": False,
                "default": self.get_option("included_tags", project) or "",
                "help": "Comma-separated tag names to show (e.g. environment,os,device). Leave empty to hide tags.",
            },
        ]

    def error_message_from_json(self, data):
        return data.get("description", "unknown error")

    def get_client(self, project):
        return TelegramClient(bot_token=self.get_option("bot_token", project))

    def _build_message(self, event, group, project):
        title = event.title[:256]
        link = group.get_absolute_url(params={"referrer": "telegram_plugin"})

        lines = [
            f"<b>{project.get_full_name()}</b>",
            f'<a href="{link}">{title}</a>',
        ]

        if self.get_option("show_level", project):
            level = event.get_tag("level") or "error"
            lines.append(f"Level: <code>{level}</code>")

        if self.get_option("show_culprit", project) and event.culprit:
            lines.append(f"Culprit: <code>{event.culprit}</code>")

        if self.get_option("show_message", project) and event.message:
            lines.append(f"Message: {event.message[:512]}")

        included_tags = self.get_option("included_tags", project)
        if included_tags:
            allowed = {t.strip() for t in included_tags.split(",") if t.strip()}
            tags = event.tags or []
            for k, v in tags:
                if k in allowed:
                    lines.append(f"<code>{k}</code>: {v}")

        return "\n".join(lines)

    def notify(self, notification: Notification, raise_exception: bool = False) -> None:
        event = notification.event
        group = event.group
        project = group.project

        text = self._build_message(event, group, project)

        client = self.get_client(project)
        chat_id = self.get_option("chat_id", project)
        topic_id = self.get_option("topic_id", project)
        message_thread_id = int(topic_id) if topic_id else None
        try:
            client.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
        except Exception as e:
            self.raise_error(e)
