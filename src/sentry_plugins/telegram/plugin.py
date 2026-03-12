import re

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

DEFAULT_MESSAGE_TEMPLATE = (
    "<b>{project}</b>\n"
    '<a href="{link}">{title}</a>\n'
    "Level: <code>{level}</code>\n"
    "Culprit: <code>{culprit}</code>"
)

TEMPLATE_HELP = (
    "HTML message template. Available variables: "
    "{project}, {title}, {link}, {level}, {culprit}, {message}, "
    "{tags} (all tags), {tag:NAME} (specific tag, e.g. {tag:environment})."
)


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
            {
                "name": "message_template",
                "label": "Message Template",
                "type": "textarea",
                "required": False,
                "default": self.get_option("message_template", project) or DEFAULT_MESSAGE_TEMPLATE,
                "help": TEMPLATE_HELP,
            },
        ]

    def error_message_from_json(self, data):
        return data.get("description", "unknown error")

    def get_client(self, project):
        return TelegramClient(bot_token=self.get_option("bot_token", project))

    def _render_template(self, template, event, group, project):
        title = event.title[:256]
        link = group.get_absolute_url(params={"referrer": "telegram_plugin"})
        level = event.get_tag("level") or "error"
        culprit = event.culprit or ""
        message = event.message or ""

        tags = event.tags or []
        tags_dict = {k: v for k, v in tags}
        tags_text = ", ".join(f"{k}={v}" for k, v in tags)

        text = template.replace("{project}", project.get_full_name())
        text = text.replace("{title}", title)
        text = text.replace("{link}", link)
        text = text.replace("{level}", level)
        text = text.replace("{culprit}", culprit)
        text = text.replace("{message}", message)
        text = text.replace("{tags}", tags_text)

        text = re.sub(
            r"\{tag:([^}]+)\}",
            lambda m: tags_dict.get(m.group(1), ""),
            text,
        )

        return text

    def notify(self, notification: Notification, raise_exception: bool = False) -> None:
        event = notification.event
        group = event.group
        project = group.project

        template = self.get_option("message_template", project) or DEFAULT_MESSAGE_TEMPLATE
        text = self._render_template(template, event, group, project)

        client = self.get_client(project)
        chat_id = self.get_option("chat_id", project)
        topic_id = self.get_option("topic_id", project)
        message_thread_id = int(topic_id) if topic_id else None
        try:
            client.send_message(chat_id=chat_id, text=text, message_thread_id=message_thread_id)
        except Exception as e:
            self.raise_error(e)
