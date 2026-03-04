from sentry_plugins.client import ApiClient


class TelegramClient(ApiClient):
    base_url = "https://api.telegram.org"
    allow_redirects = False
    plugin_name = "telegram"

    def __init__(self, bot_token):
        self.bot_token = bot_token
        super().__init__()

    def request(self, method, path, data):
        return self._request(path=path, method=method, data=data)

    def send_message(self, chat_id, text, parse_mode="HTML", message_thread_id=None):
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if message_thread_id is not None:
            data["message_thread_id"] = message_thread_id
        return self.request(
            "POST",
            f"/bot{self.bot_token}/sendMessage",
            data=data,
        )
