OA GAME ROTATOR v0.8.2.3
by Stephen Larroque
========================

OA Game Rotator is a cyclic event manager for a game server by using an event log which describes the list of events to produce, the parameters to send to the game server and the time at which they have to happen.

LICENSE
-------

This software is licensed under the Affero GNU General Public License version 3 or above (AGPLv3+).

DESCRIPTION
-----------

This is a Python 2.7 daemon, and needs oamps.sh to work. It is also advised to use it in conjunction with the companion application Game Booking Manager for the user's interface.

OA Game Rotator is made to work with OpenArena, but it should also work with any ioquake3-based game (ioUrban Terror, Tremulous, Warsow, Smoking Guns, etc...).

This application is very flexible and can be used for a wide array of cases.

To summary it up: if you want to make your game server work differently for different periods of time, this application is perfect for you.

For example: if you want that in the morning, your server plays Capture The Flag, but in the afternoon the rules changes and it plays DeathMatch, you can easily do that using OA Game Rotator.

You can also produce more complex behaviours: you can plan a random event every few minutes, like changing the gravity randomly, or anything else you want.

Another usage is to use it to book your server, meaning that for a specified period of time, the game server will run with a specific configuration and a rcon, which both will change in the next period of time.
This usage is the primary motivation behind this tool, and is an all-in-one kit to do that if you use OA Game Rotator in conjuction with Game Booking Manager and OAMPS.

USAGE
-----

Type ./python oa-game-rotator.py --help to get a full list of possible arguments.

It is also possible to use any oamps.sh option, they will be transmitted to oamps.sh automatically (check ./oamps.sh --help to get the additional list of options).

Eg:
- A simple example: python oa-game-rotator.py -x clantrain -f jobs -c q3config.cfg -d http://localhost/game-booking-manager/booking-download.php -dp password -v
- A more complex example launching a game server while also managing a GTV server automatically: python oa-game-rotator.py -x clantrain -f jobs -c q3config.cfg -d http://www.oa-community.com/oa-clan-booking/booking-download.php -dp password -v     -b /home/openarenacom/openarena/openarena-0.8.1/ --homepath /home/openarenacom/openarena/openarena-0.8.1/virtual/ -p 27980 -s oac-clantrain-server     -tv -tvs oac-clantrain-gtv -tvp 31000 -tvc oac-gtv-editme.cfg -tvm dpmaster.deathmask.net -tvmp 27950 --heartbeat --heartbeatscreen oac-clantrain-heartbeater

SPECIAL BEHAVIORS
-----------------

- Slots parameters have priority over commandline arguments: (nearly) all commandline arguments are overwritten by slots parameters (if exist)
- Exception to the previous rule: --exec and --gtvexec commandline arguments are appended, so if they also exist in a slot, they will both be appended and executed

FAQ
---

- why slots are off by a few hours from my local time?
Because time must be considered as UTC, so when you design manually your own slotsfile, do consider your timezone offset.
