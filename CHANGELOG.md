# 2019-06-07 - BitBot v1.9.0

Added:
- IRCv3: Also look at CTCP events for msgids
- Sub-event system within all SentLines
- Show last action in `!seen` (e.g. 'seen 1m ago (<jesopo> hi)')
- WARN when labels are not responded to in a timely fashion
- IRCv3: send `+draft/typing` while processing commands
- Display github `ready_for_review` better
- Parse 221 (RPL_UMODEIS) numerics

Changed:
- `!np` against a known nickname will attempt to resolve to lastfm username
- `PING` and `PONG` now avoid write throttling
- `!bang` -> `!trap`, 'shot' -> 'trapped' for ducks
- Socket reads and socket writes have been moved on to seperate threads
- Use Deques for chat history (more performant!)

Fixed:
- Differentiate between send and received CTCP events
- `IRCSocket._send` will now only return lines that definitely hit the wire
- GitHub `commit_comment` event formatting exception
- Strip xref tags from `!define` output
- `check_purge()` after removing contextual hooks from an EventHook
- IRCv3: Escape message tag values

# 2019-06-03 - BitBot v1.8.0

Added:
- Module dependency system
- Enable TCP keepalives
- IRCv3: `draft/label` tracking on every sent line when CAPs permit
- Enforce Python version 3.6.0 or later
- 'module-whitelist'/'module-blacklist' in `bot.conf`

Changed:
- IRCv3: Use last `server-time` for `RESUME` - not last .recv() time
- IRCv3: `draft/labeled-response` -> `draft/labeled-response-0.2`
- IRCv3: Prune already-seen messages in `chathistory` batches
- Consolidate `PRIVMSG`, `NOTICE` and `TAGMSG` handlers in to one

Fixed
- GitHub highlight prevention - don't detect highlights mid-word
- Pass already-decoded data in to BeautifulSoup
- !enablemodule actually removes module from blacklist setting
- Only enact write throttling when immediate-write-buffer is empty
- Non-throttled lines no longer delay throttled lines

# 2019-05-24 - BitBot v1.7.1

Fixed:
- Fix crash caused by CAP NEW

# 2019-05-23 - BitBot v1.7.0

Added:
- Add !addserver
- Add !masterpassword
- Add auto-tweet setting
- Support triggering commands by regex

Changed:
- Show usage examples for user/channel/server/bot settings
- Strip common command prefixes from PM commands so "!help" works
- Change auto-github to work for github urls too
- IRCv3: draft/resume-0.3 -> draft/resume-0.4
- Remove `ipv4` server attribute - figure it out automatically

Fixed:
- Typos/bugs in BATCH and FAIL
- Fix crash caused by BitBot messaging himself