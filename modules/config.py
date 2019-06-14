#--depends-on channel_access
#--depends-on commands
#--depends-on permissions

import enum
from src import ModuleManager, utils

CHANNELSET_HELP = "Get a specified channel setting for the current channel"

class ConfigInvalidValue(Exception):
    pass
class ConfigSettingInexistent(Exception):
    pass

class ConfigResults(enum.Enum):
    Changed = 1
    Retrieved = 2
    Removed = 3
class ConfigResult(object):
    def __init__(self, result, data=None):
        self.result = result
        self.data = data

class ConfigChannelTarget(object):
    def __init__(self, bot, server, channel_name):
        self._bot = bot
        self._server = server
        self._channel_name = channel_name
    def _get_id(self):
        return self._server.channels.get_id(self._channel_name)
    def set_setting(self, setting, value):
        channel_id = self._get_id()
        self._bot.database.channel_settings.set(channel_id, setting, value)
    def get_setting(self, setting, default=None):
        channel_id = self._get_id()
        return self._bot.database.channel_settings.get(channel_id, setting,
            default)
    def del_setting(self, setting):
        channel_id = self._get_id()
        self._bot.database.channel_settings.delete(channel_id, setting)

class Module(ModuleManager.BaseModule):
    def _to_context(self, server, channel, user, context_desc):
        context_desc_lower = context_desc.lower()
        if context_desc_lower == "user":
            return user, "set"
        elif context_desc_lower == "channel":
            return channel, "channelset"
        elif context_desc_lower == "server":
            return server, "serverset"
        elif context_desc_lower == "bot":
            return self.bot, "botset"
        else:
            raise ValueError()

    @utils.hook("preprocess.command")
    def preprocess_command(self, event):
        require_setting = event["hook"].get_kwarg("require_setting", None)
        if not require_setting == None:
            require_setting_unless = event["hook"].get_kwarg(
                "require_setting_unless", None)
            if not require_setting_unless == None:
                require_setting_unless = int(require_setting_unless)
                if len(event["args_split"]) >= require_setting_unless:
                    return

            context, _, require_setting = require_setting.rpartition(":")
            require_setting = require_setting.lower()
            channel = None
            if event["is_channel"]:
                channel = event["target"]

            target, context = self._to_context(event["server"], channel,
                event["user"], context or "user")

            export_settings = self._get_export_setting(context)
            setting_info = export_settings.get(require_setting, None)
            if setting_info:
                value = target.get_setting(require_setting, None)
                if value == None:
                    example = setting_info.get("example", "<value>")
                    return "Please set %s, e.g.: %s%s %s %s" % (
                        require_setting, event["command_prefix"], context,
                        require_setting, example)

    def _set(self, category, event, target, arg_index=0):
        args = event["args_split"][arg_index:]
        settings = self.exports.get_all(category)
        settings_dict = {setting["setting"]: setting for setting in settings}

        setting = args[0].lower()
        if setting in settings_dict:
            setting_options = settings_dict[setting]
            if len(args) > 1:
                value = " ".join(args[1:])
                value = setting_options.get("validate", lambda x: x)(value)

                if not value == None:
                    target.set_setting(setting, value)

                    self.events.on("set").on(category).on(setting).call(
                        value=value, target=target)

                    event["stdout"].write("Saved setting")
                else:
                    event["stderr"].write("Invalid value")
            elif len(args) == 1:
                example = setting_options.get("example", None)
                if example:
                    event["stderr"].write("Please provide a value, e.g. %s"
                        % example)
                else:
                    event["stderr"].write("Please provide a value")
            else:
                shown_settings = [key for key, value in settings_dict.items()
                    if not value.get("hidden", False)]
                shown_settings = sorted(shown_settings)
                event["stdout"].write("Available settings: %s" % (
                    ", ".join(shown_settings)))
        else:
            event["stderr"].write("Unknown setting")


    @utils.hook("received.command.set", help="Set a specified user setting")
    def set(self, event):
        """
        :usage: <setting> <value>
        """
        self._set("set", event, event["user"])

    @utils.hook("received.command.channelset", min_args=1, private_only=True,
        help=CHANNELSET_HELP)
    def private_channel_set(self, event):
        """
        :usage: <channel> <setting> <value>
        :channel_arg: 0
        :require_access: channelset
        :permission: channelsetoverride
        """
        channel = event["server"].channels.get(event["args_split"][0])
        self._set("channelset", event, channel, False, 1)

    @utils.hook("received.command.channelset", channel_only=True,
        help=CHANNELSET_HELP)
    def channel_set(self, event):
        """
        :usage: <setting> <value>
        :require_mode: high
        :permission: channelsetoverride
        """
        self._set("channelset", event, event["target"])

    @utils.hook("received.command.serverset",
        help="Set a specified server setting for the current server")
    def server_set(self, event):
        """
        :usage: <setting> <value>
        :permission: serverset
        """
        self._set("serverset", event, event["server"])

    @utils.hook("received.command.botset", help="Set a specified bot setting")
    def bot_set(self, event):
        """
        :help: Set a specified bot setting
        :usage: <setting> <value>
        :permission: botset
        """
        self._set("botset", event, self.bot)

    def _get(self, event, setting, qualifier, value):
        if not value == None:
            event["stdout"].write("'%s'%s: %s" % (setting,
                qualifier, str(value)))
        else:
            event["stdout"].write("'%s' has no value set" % setting)

    @utils.hook("received.command.get", min_args=1)
    def get(self, event):
        """
        :help: Get a specified user setting
        :usage: <setting>
        """
        setting = event["args_split"][0]
        self._get(event, setting, "", event["user"].get_setting(
            setting, None))

    @utils.hook("received.command.channelget", channel_only=True, min_args=1)
    def channel_get(self, event):
        """
        :help: Get a specified channel setting for the current channel
        :usage: <setting>
        :require_mode: o
        :permission: channelsetoverride
        """
        setting = event["args_split"][0]
        self._get(event, setting, " for %s" % event["target"].name,
            event["target"].get_setting(setting, None))

    @utils.hook("received.command.serverget", min_args=1)
    def server_get(self, event):
        """
        :help: Get a specified server setting for the current server
        :usage: <setting>
        :permission: serverget
        """
        setting = event["args_split"][0]
        self._get(event, setting, "", event["server"].get_setting(
            setting, None))

    @utils.hook("received.command.botget", min_args=1)
    def bot_get(self, event):
        """
        :help: Get a specified bot setting
        :usage: <setting>
        :permission: botget
        """
        setting = event["args_split"][0]
        self._get(event, setting, "", self.bot.get_setting(setting, None))

    def _unset(self, event, setting, category, target):
        settings = self.exports.get_all(category)
        settings_dict = {setting["setting"]: setting for setting in settings}
        setting = setting.lower()

        if setting in settings_dict:
            target.del_setting(setting)
            event["stdout"].write("Unset %s" % setting)
        else:
            event["stderr"].write("Unknown setting")

    @utils.hook("received.command.unset", min_args=1)
    def unset(self, event):
        """
        :help: Unset a specified user setting
        :usage: <setting>
        """
        self._unset(event, event["args_split"][0], "set", event["user"])

    @utils.hook("received.command.channelunset", min_args=1)
    def channel_unset(self, event):
        """
        :help: Unset a specified user setting
        :usage: <setting>
        :require_mode: high
        :permission: channelsetoverride
        """
        self._unset(event, event["args_split"][0], "channelset", event["user"])

    def _get_export_setting(self, context):
        settings = self.exports.get_all(context)
        return {setting["setting"].lower(): setting for setting in settings}

    def _config(self, export_settings, target, setting, value=None):
        if not value == None:
            validation = export_settings[setting].get("validate", lambda x: x)
            validated_value = validation(value)
            if not validated_value == None:
                target.set_setting(setting, validated_value)
                return ConfigResult(ConfigResults.Changed, validated_value)
            else:
                raise ConfigInvalidValue()
        else:
            unset = False
            if setting.startswith("-"):
                setting = setting[1:]
                unset = True

            existing_value = target.get_setting(setting, None)
            if not existing_value == None:
                if unset:
                    target.del_setting(setting)
                    return ConfigResult(ConfigResults.Removed)
                else:
                    return ConfigResult(ConfigResults.Retrieved, existing_value)
            else:
                raise ConfigSettingInexistent()

    @utils.hook("received.command.config", min_args=1)
    def config(self, event):
        """
        :help: Change config options
        :usage: <context>[:name] [-][setting [value]]
        """

        arg_count = len(event["args_split"])
        context_desc, _, name = event["args_split"][0].partition(":")

        setting = None
        value = None
        if arg_count > 1:
            setting = event["args_split"][1].lower()
            if arg_count > 2:
                value = " ".join(event["args_split"][2:])

        target, context = self._to_context(event["server"],
            event["target"], event["user"], context_desc)

        permission_check = utils.Check("permission", "config")

        if context == "set":
            if name:
                yield utils.Check("self", name)|permission_check
                target = event["server"].get_user(name)
            else:
                target = event["user"]
        elif context == "channelset":
            yield utils.Check("channel-mode", "o")|permission_check

            if name:
                if name in event["server"].channels:
                    target = event["server"].channels.get(name)
                else:
                    target = ConfigChannelTarget(self.bot, event["server"],
                        name)
            else:
                if event["is_channel"]:
                    target = event["target"]
                else:
                    raise utils.EventError(
                        "Cannot change config for current channel when in "
                        "private message")
        elif context == "serverset" or context == "botset":
            yield permission_check

        export_settings = self._get_export_setting(context)
        if not setting == None:
            if not setting.lstrip("-") in export_settings:
                raise utils.EventError("Setting not found")

            try:
                result = self._config(export_settings, target, setting, value)
            except ConfigInvalidValue:
                raise utils.EventError("Invalid value")
            except ConfigSettingInexistent:
                raise utils.EventError("Setting not set")

            if result.result == ConfigResults.Changed:
                event["stdout"].write("Config '%s' set to %s" %
                    (setting, result.data))
            elif result.result == ConfigResults.Retrieved:
                event["stdout"].write("%s: %s" % (setting, result.data))
            elif result.result == ConfigResults.Removed:
                event["stdout"].write("Unset setting")
        else:
            event["stdout"].write("Available config: %s" %
                ", ".join(export_settings.keys()))
