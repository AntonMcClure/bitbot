import datetime, typing
from src import IRCObject

# this should be 510 (RFC1459, 512 with \r\n) but a server BitBot uses is broken
LINE_CUTOFF = 470

class IRCArgs(object):
    def __init__(self, args: typing.List[str]):
        self._args = args

    def get(self, index: int) -> typing.Optional[str]:
        if index < 0:
            if len(self._args) > (abs(index)-1):
                return self._args[index]
        elif len(self._args) > index:
            return self._args[index]
        return None

    def __repr__(self):
        return "IRCArgs(%s)" % self._args
    def __len__(self) -> int:
        return len(self._args)
    def __getitem__(self, index: int) -> str:
        return self._args[index]
    def __setitem__(self, index: int, value: str):
        self._args[index] = value

class Hostmask(object):
    def __init__(self, nickname: str, username: str, hostname: str,
            hostmask: str):
        self.nickname = nickname
        self.username = username
        self.hostname = hostname
        self.hostmask = hostmask
    def __repr__(self):
        return "Hostmask(%s)" % self.__str__()
    def __str__(self):
        return self.hostmask

class ParsedLine(object):
    def __init__(self, command: str, args: typing.List[str],
            prefix: Hostmask=None,
            tags: typing.Dict[str, str]=None):
        self.command = command
        self._args = args
        self.args = IRCArgs(args)
        self.prefix = prefix
        self.tags = {} if tags == None else tags

    def _tag_str(self, tags: typing.Dict[str, str]) -> str:
        tag_pieces = []
        for tag, value in tags.items():
            if value:
                tag_pieces.append("%s=%s" % (tag, value))
            else:
                tag_pieces.append(tag)

        if tag_pieces:
            return "@%s" % ",".join(tag_pieces)
        return ""

    def format(self) -> str:
        pieces = []
        if self.tags:
            pieces.append(self._tag_str(self.tags))

        if self.prefix:
            pieces.append(str(self.prefix))

        pieces.append(self.command.upper())

        if self.args:
            for i, arg in enumerate(self._args):
                if arg and i == len(self._args)-1 and (
                        " " in arg or arg[0] == ":"):
                    pieces.append(":%s" % arg)
                else:
                    pieces.append(arg)

        return " ".join(pieces).split("\n")[0].strip("\r")

class SentLine(IRCObject.Object):
    def __init__(self, send_time: datetime.datetime, hostmask: str,
            line: ParsedLine):
        self.send_time = send_time
        self._hostmask = hostmask
        self.parsed_line = line

        self._on_send: typing.List[typing.Callable[[], None]] = []
        self.truncate_marker: typing.Optional[str] = None

    def __repr__(self) -> str:
        return "IRCLine.SentLine(%s)" % self.__str__()
    def __str__(self) -> str:
        return self.decoded_data()

    def _char_limit(self) -> int:
        return LINE_CUTOFF-len(":%s " % self._hostmask)

    def _encode_truncate(self) -> typing.Tuple[bytes, str]:
        line = self.parsed_line.format()
        byte_max = self._char_limit()
        encoded = b""
        truncated = ""
        truncate_marker = b""
        if not self.truncate_marker == None:
            truncate_marker = typing.cast(str, self.truncate_marker
                ).encode("utf8")

        for i, character in enumerate(line):
            encoded_character = character.encode("utf8")
            new_len = len(encoded + encoded_character)
            if truncate_marker and (byte_max-new_len) < len(truncate_marker):
                encoded += truncate_marker
                truncated = line[i:]
                break
            elif new_len > byte_max:
                truncated = line[i:]
                break
            else:
                encoded += encoded_character
        return (encoded, truncated)

    def _data(self) -> bytes:
        return self._encode_truncate()[0]
    def data(self) -> bytes:
        return b"%s\r\n" % self._data()
    def decoded_data(self) -> str:
        return self._data().decode("utf8")
    def truncated(self) -> str:
        return self._encode_truncate()[1]

    def on_send(self, func: typing.Callable[[], None]):
        self._on_send.append(func)
    def sent(self):
        for func in self._on_send[:]:
            func()
