from src import utils

def handle_311(event):
    nickname = event["args"][1]
    username = event["args"][2]
    hostname = event["args"][3]
    realname = event["args"][4]

    if event["server"].is_own_nickname(nickname):
        event["server"].username = username
        event["server"].hostname = hostname
        event["server"].realname = realname

    target = event["server"].get_user(nickname)
    target.username = username
    target.hostname = hostname
    target.realname = realname

def quit(events, event):
    nickname = None
    if event["direction"] == utils.Direction.Recv:
        nickname = event["source"].nickname
    reason = event["args"].get(0)

    if event["direction"] == utils.Direction.Recv:
        nickname = event["source"].nickname
        if (not event["server"].is_own_nickname(nickname) and
                not event["source"].hostmask == "*"):
            user = event["server"].get_user(nickname)
            events.on("received.quit").call(reason=reason, user=user,
                server=event["server"])
            event["server"].remove_user(user)
        else:
            event["server"].disconnect()
    else:
        events.on("send.quit").call(reason=reason, server=event["server"])

def nick(events, event):
    new_nickname = event["args"].get(0)
    user = event["server"].get_user(event["source"].nickname)
    old_nickname = user.nickname

    if not event["server"].is_own_nickname(event["source"].nickname):
        events.on("received.nick").call(new_nickname=new_nickname,
            old_nickname=old_nickname, user=user, server=event["server"])
    else:
        events.on("self.nick").call(server=event["server"],
            new_nickname=new_nickname, old_nickname=old_nickname)
        event["server"].set_own_nickname(new_nickname)

    user.set_nickname(new_nickname)
    event["server"].change_user_nickname(old_nickname, new_nickname)

def away(events, event):
    user = event["server"].get_user(event["source"].nickname)
    message = event["args"].get(0)
    if message:
        user.away = True
        user.away_message = message
        events.on("received.away.on").call(user=user, server=event["server"],
            message=message)
    else:
        user.away = False
        user.away_message = None
        events.on("received.away.off").call(user=user, server=event["server"])

def chghost(event):
    nickname = event["source"].nickname
    username = event["args"][0]
    hostname = event["args"][1]

    if event["server"].is_own_nickname(nickname):
        event["server"].username = username
        event["server"].hostname = hostname

    target = event["server"].get_user(nickname)
    target.username = username
    target.hostname = hostname

def setname(event):
    nickname = event["source"].nickname
    realname = event["args"][0]

    user = event["server"].get_user(nickname)
    user.realname = realname

    if event["server"].is_own_nickname(nickname):
        event["server"].realname = realname

def account(events, event):
    user = event["server"].get_user(event["source"].nickname)

    if not event["args"][0] == "*":
        user.identified_account = event["args"][0]
        user.identified_account_id = event["server"].get_user(
            event["args"][0]).get_id()
        events.on("received.account.login").call(user=user,
            server=event["server"], account=event["args"][0])
    else:
        user.identified_account = None
        user.identified_account_id = None
        events.on("received.account.logout").call(user=user,
            server=event["server"])
