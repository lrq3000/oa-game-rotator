OA GAME ROTATOR v0.8.3
========================
by Stephen Larroque

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

EXAMPLE SLOTS FILE
--------------------------------

Slots files are the core part of this application. This is where you specify what you want to do, and when you want these events to happen.

The syntax of a slots file is very simple. On the first line, you set the total number of slots. On all the others, you define the events.

Here is an example of a 4 slots file:

    4
    slot0: empty
    slot1: empty
    slot2: empty
    slot3: empty

Since there are 4 slots, the day will be divided in 4, and thus one slot represent one event every 6 hours (24/4).

This slots file is very simple and doesn't do anything.

Now here is a more interesting 4 slots file:

    4
    slot0: restart_hard|gamemod=baseoa|config=myconfigbaseoa.cfg|exec=set g_gametype 2;map_restart
    slot1: restart_hard|gamemod=aftershock|config=myconfigas.cfg|exec=set g_gametype 5;map_restart
    slot2: restart_hard|gamemod=excessiveplus|config=myconfigeplus.cfg|exec=set g_gametype 4;map_restart|password=crowned-six-spur
    slot3: restart_soft|exec=set g_gametype 2;map_restart

This slots file change the whole gamemod and gametype for each event:

- in the first 6 hours, the server will play with baseoa gamemod, using myconfigbaseoa.cfg as a config file, and in Tourney gametype;
- between 6AM and 12AM, the server will play with AfterShock gamemod, using myconfigas.cfg and in ClanArena gametype;
- between 12AM and 6PM, the server will play with ExcessivePlus gamemod, using myconfigeplus.cfg and in CTF gametype, and with a private password being "crowned-six-spur";
- and finally between 6PM and 12PM, the last gamemod and the exact same config will be kept (ExcessivePlus gamemod and myconfigeplus.cfg in CTF), but this time without a private password, the server will become public again (because if you don't provide a password for a slot, it is automatically implied that there's no password for this slot).

A few notes:

- Note that the delimiter is "|" (which can be easily changed in the script, but if you use the companion webapp game-booking-manager you'd rather not because using "|" is safe, there are checks in game-booking-manager).
- Note also the restart_hard and restart_soft special options. restart_hard is when you need to switch the mod, and thus want to do a full restart. restart_soft is when you want to softly restart without disconnecting the clients (ie: it does a simple map_restart). Generally, prefer using restart_soft whenever possible, and only use restart_hard if you switch mods.
- exec is the ioquake3's exec argument. Thus you can pass any additionnal ioquake3 command and cvar directly in your slots (eg: you can add a special chat line to happen at a specified time event).

MULTIPLE SLOTS FILES
---------------------------

What if you want to not only have different events per time of the day, but also different events for every days, or every months?

You can easily do that by using a different filename.

For example, if your slots file is named like:

- myslotsfile.txt : Your events will be executed everydays of every years and everytime.
- myslotsfile-2013.txt : Your events will be executed everydays but only during year 2013, but not during year 2012 or 2014.
- myslotsfile-2013-02.txt : Your events will be executed everydays but only during the whole month February 2013, but not on March or January.
- myslotsfile-2013-02-24.txt : Your events will be executed only during one day, the 24th February 2013, but not the 23th or the 25th.

Also, these files are complementary: this application will search for the most specific slots file (eg: myslotsfile-2013-02-24.txt) but if not found it will try to find a more general one (eg: myslotsfile-2013-02.txt).

For example, you can have multiple slots files sitting together in the slots folder, like this:

    slots/
        myslotsfile-2013-02-24.txt
        myslotsfile-2013-02.txt
        myslotsfile.txt

This configuration will work like this:

- On the 24th February 2013, myslotsfile-2013-02-24.txt will be executed (so it's a very special day!).
- On every other day of February 2013, myslotsfile-2013-02.txt.
- On every other day _except_ February 2013, myslotsfile.txt will be executed (it's a bit like a default config file).

SPECIAL BEHAVIORS
-----------------

- Slots parameters have priority over commandline arguments: (nearly) all commandline arguments are overwritten by slots parameters (if exist)
- Exception to the previous rule: --exec and --gtvexec commandline arguments are appended, so if they also exist in a slot, they will both be appended and executed

FAQ
---

- why slots are off by a few hours from my local time?
Because time must be considered as UTC, so when you design manually your own slotsfile, do consider your timezone offset.
