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
        ]

    def get_client(self, project):
        return TelegramClient(bot_token=self.get_option("bot_token", project))

    def notify(self, notification: Notification, raise_exception: bool = False) -> None:
        event = notification.event
        group = event.group
        project = group.project

        title = event.title[:256]
        link = group.get_absolute_url(params={"referrer": "telegram_plugin"})
        level = event.get_tag("level") or "error"
        culprit = event.culprit or ""

        text = (
            f"<b>{project.get_full_name()}</b>\n"
            f"<a href=\"{link}\">{title}</a>\n"
            f"Level: <code>{level}</code>\n"
        )
        if culprit:
            text += f"Culprit: <code>{culprit}</code>\n"

        client = self.get_client(project)
        chat_id = self.get_option("chat_id", project)
        try:
            client.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            self.raise_error(e)
