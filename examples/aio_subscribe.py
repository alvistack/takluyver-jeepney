# See the blocking example for a note on match rules.

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate, Proxy
from jeepney.bus_messages import DBus, MatchRule
from aio_notify import Notifications

some_words = ('Beautiful', 'implicit', 'complicated', 'Readability',
              'practicality', 'silently', 'explicitly', 'silenced',
              'ambiguity', 'temptation', 'preferably', 'obvious',
              'implementation', 'Namespaces')


def print_match(*args, idees, seen):
    """A demo callback.

    More info: <https://developer.gnome.org/notification-spec>
    """
    reasons = (
        "Expired",
        "Dismissed by the user",
        "Closed by a call to CloseNotification",
        "Undefined/reserved reasons"
    )
    idee, reason = args[0]

    assert len(args) == 1
    assert type(idee) is int and type(reason) is int
    assert (idee, reason) not in seen
    assert idee == idees[-1]

    word = idee - idees[0]
    widths = print_match.widths
    print("<- ID: {:{dlen}}, Word: {:{wlen}} Reason: {!r}."
          .format(idee, "%r," % some_words[word], reasons[reason], **widths))
    seen.add((idee, reason))


async def main():
    __, proto = await connect_and_authenticate("SESSION")
    session_bus = Proxy(DBus(), proto)
    notify_service = Proxy(Notifications(), proto)

    # Create a "signal-selection" match rule used by *Match methods below
    match_rule = MatchRule(
        type="signal",
        sender=notify_service._msggen.bus_name,
        interface=notify_service._msggen.interface,
        member="NotificationClosed",
        path=notify_service._msggen.object_path,
    )

    # Prep and register callback
    idees = []
    maxit = 6  # stop subscribing after this many turns
    from functools import partial
    callback = partial(print_match, idees=idees, seen=set())
    proto.router.subscribe_signal(
        callback=callback,
        path=notify_service._msggen.object_path,
        interface=notify_service._msggen.interface,
        member="NotificationClosed"
    )

    for num, tag in enumerate(some_words, 1):
        # Mute log entries for outgoing messages while subscribed
        if num <= 1 or num > maxit:
            print("-> {:2}, {!r}".format(num, tag))

        resp = await notify_service.Notify("jeepney_test", 0, "",
                                           "Test #: %d" % num,
                                           "Message: %r" % tag,
                                           [], {}, -1,)
        sent_id, *__ = resp

        if not idees:
            from math import log10, ceil
            print_match.widths = dict(wlen=max(len(w) for w in some_words) + 1,
                                      dlen=ceil(log10(sent_id + maxit)))

        idees.append(sent_id)
        await asyncio.sleep(3/num)  # shift gears
        await notify_service.CloseNotification(sent_id)

        if num == 1:
            assert tuple() == await session_bus.AddMatch(match_rule)  # success
            print("/* Starting subscription after 1 turn */")

        if num == maxit:
            assert tuple() == await session_bus.RemoveMatch(match_rule)
            print("/* Cancelling subscription after %d turns */" % maxit)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
