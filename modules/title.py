#--depends-on commands
#--depends-on config

import hashlib, re, urllib.parse
from src import EventManager, ModuleManager, utils

@utils.export("channelset", {"setting": "auto-title",
    "help": "Disable/Enable automatically getting info titles from URLs",
    "validate": utils.bool_or_none, "example": "on"})
@utils.export("channelset", {"setting": "title-shorten",
    "help": "Enable/disable shortening URLs when getting their title",
    "validate": utils.bool_or_none, "example": "on"})
@utils.export("channelset", {"setting": "auto-title-first",
    "help": ("Enable/disable showing who first posted a URL that was "
        "auto-titled"),
    "validate": utils.bool_or_none, "exaple": "on"})
class Module(ModuleManager.BaseModule):
    def _url_hash(self, url):
        return "sha256:%s" % hashlib.sha256(url.lower().encode("utf8")
            ).hexdigest()

    def _get_title(self, channel, url):
        if not urllib.parse.urlparse(url).scheme:
            url = "http://%s" % url

        hostname = urllib.parse.urlparse(url).hostname
        if utils.http.is_localhost(hostname):
            self.log.warn("tried to get title of localhost: %s", [url])
            return None

        try:
            page = utils.http.request(url, soup=True)
        except utils.http.HTTPWrongContentTypeException:
            return None
        except Exception as e:
            self.log.error("failed to get URL title: %s", [url], exc_info=True)
            return None
        if page.data.title:
            title = page.data.title.text.replace("\n", " ").replace(
                "\r", "").replace("  ", " ").strip()

            if channel.get_setting("title-shorten", False):
                short_url = self.exports.get_one("shortlink", lambda x: x
                    )(url)
                return "%s - %s" % (title, short_url)
            return title
        else:
            return None

    @utils.hook("command.regex", ignore_action=False,
        priority=EventManager.PRIORITY_MONITOR)
    def channel_message(self, event):
        """
        :command: title
        :pattern-url: 1
        """
        if event["target"].get_setting("auto-title", False):
            event.eat()
            url = event["match"].group(0)
            title = self._get_title(event["target"], event["match"].group(0))

            if title:
                message = title
                if event["target"].get_setting("auto-title-first", False):
                    setting = "url-last-%s" % self._url_hash(url)
                    first_details = event["target"].get_setting(setting, None)

                    if first_details:
                        first_nickname, first_timestamp, _ = first_details
                        timestamp_parsed = utils.iso8601_parse(first_timestamp)
                        timestamp_human = utils.datetime_human(timestamp_parsed)
                        message = "%s (first posted by %s at %s)" % (title,
                            first_nickname, timestamp_human)
                    else:
                        event["target"].set_setting(setting,
                            [event["user"].nickname, utils.iso8601_format_now(),
                            url])
                event["stdout"].write(message)

    @utils.hook("received.command.t", alias_of="title")
    @utils.hook("received.command.title", usage="[URL]")
    def title(self, event):
        """
        :help: Get the title of a URL
        :usage: [URL]
        """
        url = None
        if len(event["args"]) > 0:
            url = event["args_split"][0]
        else:
            url = event["target"].buffer.find(utils.http.REGEX_URL)
            if url:
                url = re.search(utils.http.REGEX_URL, url.message).group(0)
        if not url:
            raise utils.EventError("No URL provided/found.")

        title = self._get_title(event["target"], url)

        if title:
            event["stdout"].write(title)
        else:
            event["stderr"].write("Failed to get title")
