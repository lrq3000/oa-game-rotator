#!/usr/bin/env python
#
# OpenArena Game Rotator
# Copyright (C) 2011-2013 Larroque Stephen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the Affero GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#=================================
#               OpenArena Game Rotator
#      by Stephen Larroque alias GrosBedo
#               License: Affero GPL v3+ (AGPLv3 or Above)
#              Creation date: 2011-12-29
#          Last modification: 2013-04-13
#                     version: 0.8.3
#=================================

# Import necessary libraries
import argparse
import os, datetime, time, sys
import math, re
import pprint # Unnecessary, used only for debugging purposes

#***********************************
#                   FUNCTIONS
#***********************************

# Redirect print output to the terminal as well as in a log file
class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.file.flush()
        self.stdout.write(data)

# UNUSED: for argparse to return a fullpath (absolute) instead of a relative path
class FullPaths(argparse.Action):
    """Expand user- and relative-paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))

# Check that an argument is a real directory
def is_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname

# UNUSED - example of argparse using fullpath class to check and get absolute paths to folders
def get_args():
    """Get CLI arguments and options"""
    parser = argparse.ArgumentParser(description="""do something""")

    parser.add_argument('alignments', help="The folder of alignments",
        action=FullPaths, type=is_dir)

# Relative path to absolute
def fullpath(relpath):
    if (type(relpath) is object or type(relpath) is file):
        relpath = relpath.name
    return os.path.abspath(os.path.expanduser(relpath))

# Convert a given time to a slot's number
def convert_time_to_slots(time, minutes_per_slot, separator):
    [hours, minutes] = time.split(separator);

    minutes = int(int(minutes)+(int(hours)*60));

    return int(math.floor(minutes/minutes_per_slot));

# Convert slots to relative time for the day (so there's no day attached, you must do yourself the combination)
def convert_slots_to_time(slots, minutes_per_slot, separator, hideemptyminutes = False):
    hours = (slots*minutes_per_slot)/60;
    if (hours > 0): # if the number is positive, we floor the number of hours (so we can get something like 0:30)
        hours = int(math.floor(hours));
    else: # else if the number is negative (eg: timezones), we truncate to the ceiling the number of hours (so we can get something like -0:30)
        hours = int(math.ceil(hours));
    hours = str(hours).rjust(2, '0')

    minutes = abs((slots*minutes_per_slot)%60) # get the number of minutes from the slots. We get the absolute value because else we may get something like -1:-30, which is not a human format, the valid one would be -1:30
    minutes = str(minutes).rjust(2, '0')

    if (hideemptyminutes and minutes == 0):
        return hours+separator;
    else:
        return separator.join([str(hours), str(minutes)]);

# Port of PHP array_pad - UNUSED
# from http://www.php2python.com/
def array_pad(lst, size, value):
    if size >= 0:
        return lst.extend([value] * (size - len(lst)))
    else:
        return [value] * (-size - len(lst)) + lst

# Function that reads a string line containing parameters with values and returns an array in the format :
# params['param'] = 'value'
def read_params(line, delimiter, assign):
    # Fetching all the parameters and values of the event (one event per line)
    r = re.compile('(?P<param>\w+)('+assign+'(?P<value>[^'+delimiter+']+))?')

    params = dict()

    for match in r.finditer(line):
        # If we get no match then we just return the line as it is
        if (match.group('param').strip() is None):
            return line
        # If the line only contain an Empty parameter or Reserved (unconfirmed reservation), we return None too
        elif (match.group('param').strip() == 'empty' or match.group('param').strip() == 'reserved'):
            return None
        # Else, if we've matched
        else:
            # If the parameter has no value, we just return the parameter (because it takes no parameter, such as restart_soft)
            if not match.group('value'):
                params[match.group('param')] = None
            # Else, if there's a value for this parameter, we assign it to the parameter
            else:
                # Formatting the datas of the event and storing inside a new event in the events array
                params[match.group('param')] = match.group('value')

    # Return the parameters/values list
    return params

# Read today's slots file and return the total number of slots, and a list of slots with each slot containing itself a list of parameters
# if error, it returns an None object
# This function will try first to read today's slotfile, then month slotfile, than year slotfile, then just the server slotfile
# eg: for server clantrain,:
# 1/ clantrain-2011-12-29.txt
# 2/ clantrain-2011-12.txt
# 3/ clantrain-2011.txt
# 4/ clantrain.txt
def read_slotsfile(slotsfolder, servername, delimiter, assign):

    # == Preparing the necessary things to read and parse the slots file
    # Get today's date
    d = datetime.datetime.utcnow()
    today = d.strftime("%Y-%m-%d")
    month = d.strftime("%Y-%m")
    year = d.strftime("%Y")

    # Get the different slotsfiles (today, month, year, and then general server slotfile)
    todayslotsfilename = os.path.join(slotsfolder,servername+'-'+today+'.txt')
    monthslotsfilename= os.path.join(slotsfolder,servername+'-'+month+'.txt')
    yearslotsfilename= os.path.join(slotsfolder,servername+'-'+year+'.txt')
    serverslotsfilename= os.path.join(slotsfolder,servername+'.txt')

    # Select the first slotsfile that exists
    slotsfilename = None

    if (os.path.exists(todayslotsfilename)):
        slotsfilename = todayslotsfilename
    elif (os.path.exists(monthslotsfilename)):
        slotsfilename = monthslotsfilename
    elif (os.path.exists(yearslotsfilename)):
        slotsfilename = yearslotsfilename
    else:
        return None # If none was found, we return None (meaning we have no booking at all)

    # Read the slotsfile
    slotsfile = open(slotsfilename, 'r')

    # try to read the file, if empty, it will return None
    try:
        # Get the total number of slots: The first line of the slots file always contain the header = the number of slots
        nbslots = int(slotsfile.readline().strip())
    except:
        return None

    # Read all the other lines and store them in a lines list (each line containing the full description of a slot)
    lines = slotsfile.read().split('\n')

    # Initializing the slots list
    slots = [None]*nbslots

    # Precompile the regular expression (will make things faster since we will use it several times)
    r = re.compile(r'slot(?P<slotnb>\d+):\s*(?P<args>.+)?')

    # == Parsing the slots file and affecting the slots list (each slot will contain a list of parameters and values)
    # Reading one line at a time
    for line in lines:
        # matching the slots format with a regexp
        matchs = r.match(line)

        # If the line contains a valid slot number (skipping the header), we append the slot arguments to our array
        if matchs is None: # here there's no valid regexp matching, we skip
            return None
        else: # valid matching of regexp, we continue
            if matchs.group('slotnb'): # valid slot number, we continue
                slotindex = int(matchs.group('slotnb')) # store the slot number
                if not matchs.group('args').strip(): # if the line is empty, ...
                    slots[slotindex] = '' # we set an empty slot
                else:
                    slots[slotindex] = read_params(matchs.group('args').strip(), delimiter, assign) # else we parse the parameters (can return an empty slot too if the param is "empty")

    slotsfile.close() # Closing the slots file

    # == Check if all slots are empty
    countempty = 0
    for slot in slots:
        if slot is None:
            countempty += 1

    # If the slots are all empties, then we return None
    if countempty == nbslots: # FIXME: if you don't want the script to continue to check the remote server when the slotsfile is available but empty, remove this condition
        return None
    # Else we return the total number of slots and the slots array containing the parameters for the server
    else:
        return [nbslots, slots]

# Get today's date (as a datetime object and two strings: one for date and one for time)
def get_today(timedelimiter=":", margindelay = 0):
    d = datetime.datetime.utcnow()
    if margindelay and margindelay != 0: # if we have set an offset (in seconds), then we move the date so that we can return the right time (useful for countdown parameter)
        d = d-datetime.timedelta(seconds=margindelay)
    today = d.strftime("%Y-%m-%d")
    currtime = d.strftime("%H"+timedelimiter+"%M")

    return [d, today, currtime]

# Get the slots file name and path
def get_slotsfilename(start_date, slotsfolder, servername):
    return os.path.join(slotsfolder,servername+'-'+start_date+'.txt')

# Remotely download a slot file (containing the booking data, see jobs/ folder for a dummy file)
def download_slotsfile(slotsfolder, servername, start_date, download_url, download_password):
    import urllib2
    try:
        download_fullurl = download_url+'?server_name='+servername+'&password='+download_password+'&start_date='+start_date
        print("Downloading slotsfile from: "+download_fullurl)
        # Download the slots file
        response = urllib2.urlopen(download_fullurl, timeout=10)
        slots = response.read() # store the file in a list
        response.close() # close the remote file
        # Save the remote slots file into a local slots file
        slotsfilepath = get_slotsfilename(start_date, slotsfolder, servername)
        f = open(slotsfilepath, 'w')
        f.write(slots)
        f.flush() # refresh the file (so that the lines get written in, close() do the same)
        f.close() # outputs and synchronize the filewriting (else, if we try to later read the same file, it will be empty)
        slots = None # delete the temporary list
    # If there's an error (probably because we can't download the file)
    except Exception as inst:
        # If we tried to download today's slotsfile, we show a different message error (more significant for debugging)
        [d, today, currtime] = get_today()
        if (start_date == today):
            print('ERROR: Could not remotely download today\'s slots file. Maybe noone booked today? Error:'+str(inst))
        # Else if we've tried to download any other day's slotfile, we show the specified date
        else:
            print('ERROR: Could not remotely download '+start_date+' slots file. Maybe noone booked that day? Error:'+str(inst))

# Autodetection of slots time and sleep time (the program will automatically sleep the time between each slot, so that no resource is used meanwhile)
def get_slots_time_infos(nbslots, timedelimiter = ":", margindelay = 0):
    # Get date and time
    [d, today, currtime] = get_today(timedelimiter, margindelay) # date and time with offset (margindelay)

    # Important var for conversion slots into time and inversely, do not touch!
    minutes_per_slot = 1440/nbslots

    # Get current slot (from current time)
    currslot = convert_time_to_slots(currtime, minutes_per_slot, timedelimiter)

    # Get next slot
    nextslot = (currslot + 1) % nbslots

    # Convert the next slot and get the next time when the next slot will happen
    nexttimestr = convert_slots_to_time(nextslot, minutes_per_slot, timedelimiter)
    if nextslot < currslot: # If the nextslot is lesser than the current slot, then it means that the nextslot happens tomorrow
        # Compute the time object of the next day
        one_day = datetime.timedelta(days=1) # the value of one day for datetime object
        d2 = d + one_day # add one day to today
        tomorrow = d2.strftime("%Y-%m-%d") # get tomorrow string
        nexttime = d.strptime(tomorrow+" "+nexttimestr, "%Y-%m-%d %H"+timedelimiter+"%M") # get next slot's time in a datetime object
    else: # else, the next slot happens today
        nexttime = d.strptime(today+" "+nexttimestr, "%Y-%m-%d %H"+timedelimiter+"%M")
    # Compute the difference to wait between the next slot's time and current time
    difftime = nexttime - d
    # Compute the sleeptime (simply the difftime in seconds + 2 minutes)
    sleeptime = difftime.seconds # exact time to wait until the end of the current slot to the next

    return [currslot, nextslot, nexttime, nexttimestr, sleeptime]

# Function that makes sure to wait until the next slot happens, and print infos in the console
def slotwait(nbslots, timedelimiter = ":", margindelay = 0):
    [currslot, nextslot, nexttime, nexttimestr, sleeptime] = get_slots_time_infos(nbslots, timedelimiter, margindelay)
    #-- Sleep the time between each slot
    print('Sleeping until next slot '+str(nextslot)+' at '+nexttimestr+' UTC (with a margin delay of '+str(margindelay)+' seconds)')
    # DEPRECATED: realsleeptime = sleeptime+margindelay*2+3 # we wait  a few minutes (in margindelay) after the planned end of a booking to make sure that after the sleep, we are in the next slot (we always wait at least 3 seconds because else most of the time we will wake up a bit earlier than intended)
    if sleeptime > 0: # sometimes, the time that it takes to execute the commands, the nextslot may already be a little behind in the past (for example at first launch, or because of countdown or execdelay or gtvexecdelay, etc.). In this case, we get a negative sleeptime, we skip the waiting
        time.sleep(sleeptime+5)  # waiting, sparing CPU cycles... Plus we wait a few more seconds because the sleep function may not be exact, and we may wakeup a bit earlier, so this hardcoded delay fix this problem most of the time
    # Check that we've slept the right amount of time, else we sleep again
    while (datetime.datetime.utcnow() < nexttime+datetime.timedelta(seconds=margindelay)): #nexttime+datetime.timedelta(seconds=margindelay)
        print('Awakening too early, waiting for another minute...')
        time.sleep(60)
    return

# Outputs a string of commands to reconnect a gtv server
def gtv_reconnect(servport, servaddr = "localhost", password = ''):
    gtvingamecommands = []
    if servport:
        if type(servport) == list: servport = servport[0]
        # The only technic to change the connection password of a gtv server, is to disconnect all games, and recreate them
        for i in range(0,12):
            gtvingamecommands.append('gtv_disconnect') # disconnect all games (12 should be enough)
        if password and password != '':
            gtvingamecommands.append('gtv_connect '+servaddr+':'+servport+' "'+password+'"') # reconnect, but this time with the new password
        else:
            gtvingamecommands.append('gtv_connect '+servaddr+':'+servport) # reconnect without password
    return gtvingamecommands


# Construct one or several string containing the commands to be executed (for booking)
last_binfullpath = ''
last_gtvfullpath = ''
def make_oamps_command(defaultconfig, defaultmod, oampsarguments, slot = None, startup = False, oampsfullpath = None):

    #-- Special variables
    refarray = ["g_refPassword", "refereePassword", "ref_password"] # store the variables that contains the referee passwords. Add here more variables to support more mods. Currently supports: AfterShock, ExcessivePlus, CPMA
    default_cmddelay = 5 # default time to wait after restarting the game server before sending the commands to set password and map restart (can be overriden by using --execdelay at commandline)
    default_gtvcmddelay = 20 # default time to wait after changing game server password and map restart before reconnecting GTV (can be overriden by using --gtvexecdelay at commandline)

    #-- Initializing variables
    # Copy oampsarguments (so that we don't touch the original dictionary)
    oampsargs = oampsarguments.copy()

    # Get environment var for the bash binary
    bashbin = os.getenv('SHELL', 'bash')

    # Get this script's directory
    currentdir = os.path.dirname(os.path.abspath(__file__))

    # OAMPS base command stores the basic command to execute the oamps.sh script (with bash binary and oamps full path if specified)
    if oampsfullpath:
        basecommand = bashbin+' '+oampsfullpath
    else: # default to the current directory
        basecommand = bashbin+' '+os.path.join(currentdir,'oamps.sh')

    # Parameters arrays and dictionaries
    oampsparams = dict()
    gtvparams = dict()
    ingamecommands = []
    gtvingamecommands = []

    # Final command strings (will be completed at the very end)
    command = basecommand
    gtvcommand = basecommand + ' -n 0 --gtv'

    # Vars that stores how many times we will repeat the sending of the commands. By default 1, but can be modified in a slotsfile with repeatX parameter.
    # mainly used restart the server (game or gtv) multiple times, this is used in case of multiple consecutive restarts such as for aftershock, which lags as hell if restarted only once
    cmdrepeat = 1
    gtvcmdrepeat = 1

    # Vars that store the last status
    # useful for restarting the server only when needed, such as when we change the binary in slotsfile (eg: enable multiview for gtv only for cpma and excessiveplus)
    # note: this could be replaced by properties in a class, and this should be cleaner, but this would be a lot more clunky and we use these variables only sparingly
    global last_binfullpath
    global last_gtvfullpath

    #-- Make oamps arguments from commandline
    # we take commandline arguments from oa-game-rotator that are the same for oamps, and feed them to oamps
    if oampsargs is not None:
        for parameter, value in oampsargs.iteritems():
            if value != False and value is not None:
                # Set the right value for the parameter: if this is only a boolean (no argument, no value), we just set an empty value, else we get the value
                if value == True:
                    value = ''
                else:
                    if type(value) == list: # since we get the params and values from argparse, it has the bad habit of always creating a list for values even if it's a single value, so here if that's the case, we fetch the single value inside the list
                        value = str(value[0])
                    else:
                        value = str(value)

                # special case: if we pass in the --exec argument, we must put it in the ingamecommands array
                if parameter == 'exec':
                    ingamecommands.append(value)
                elif parameter == 'gtvexec':
                    gtvingamecommands.append(value)
                # special case: if this is a gtv command (except gtvexec that must be treated separately, and before), we put it in the gtvparams dictionnary
                elif 'gtv' in str(parameter) or 'heartbeat' in str(parameter):
                    gtvparams[str(parameter)] = value
                # special case: if verbose, this should be applied to all commands: for game server and gtv server
                elif parameter == 'verbose':
                    oampsparams[str(parameter)] = value
                    gtvparams[str(parameter)] = value
                # general case: we just pass on the commandline parameters to oamps as they are
                else:
                    oampsparams[str(parameter)] = value

    #-- Make booking arguments
    # read the slotsfile (more precisely the slot array containing the parameters for the current slot) and parse it to form oamps parameters (can override arguments from commandline) and ingame commands (such as a soft restart by reloading the config)
    # also forms the GTV parameters
    if slot is None: # default config (when there's no slots file or when the slot is empty)
        oampsparams['config'] = defaultconfig
        if defaultmod is not None and defaultmod != '': oampsparams['gamemod'] = defaultmod
        ingamecommands.append('seta g_password ""')
        for refsetting in refarray:
            ingamecommands.append('seta ' + str(refsetting) + ' ""')
    else: # reading parameters from the slot (and eventually override commandline arguments)
        for parameter, value in slot.iteritems():
            # convert value to string
            value = str(value)

            # Booking parameters
            if parameter == 'password':
                ingamecommands.append('seta g_password "'+value+'"') # NEVER use a single quote in Q3 commands, always double quote (but in bash we can use single quotes)
            elif parameter == 'refpassword':
                for refsetting in refarray:
                    ingamecommands.append('seta ' + str(refsetting) + ' "' + value + '"')
            elif 'repeat' in parameter and len(parameter) > len('repeat'):
                # Multiple repeat: repeatx with x the number of consecutive resending of the same command, particularly useful to restart twice an AfterShock server (eg: repeat2)
                cmdrepeat = int(parameter.replace('repeat', ''))
            elif parameter == 'restart_hard':
                # A hard restart will completely shutdown the server and restart it with the given arguments (this is necessary to change mod) #FIXME: with ioquake3 it's possible to use game_restart <mod>
                oampsparams['restart'] = ''
            elif parameter == 'restart_soft':
                # A soft restart consists in reloading the config and restart the map (and resetting g_password if none is specified)
                if slot.has_key('config'):
                    conf = slot['config']
                else:
                    conf = defaultconfig
                if not slot.has_key('password'): # If there's no g_password for this session, we reset the g_password
                    ingamecommands.append('seta g_password ""')
                if not slot.has_key('refpassword'): # If there's no ref_password for this session, we reset the ref_password
                    ingamecommands.append('seta ref_password ""')
                    ingamecommands.append('seta refereePassword ""')
                ingamecommands.append('exec '+conf) # execing the config
                ingamecommands.append('map_restart') # restarting the map for the changes to take effect (it's a soft restart, so we have to do that)
                # reconnect GTV now that the server become public again (in the case the previous booking disabled GTV, if it didn't, GTV should still be able to connect without a change)
                if oampsargs.has_key('port'): gtvingamecommands.extend(gtv_reconnect(oampsargs['port']))

            # GTV management (if gtv is enabled, we must do a lot of stuff to activate/disable it on the booked server)
            elif parameter == 'gtv' and value == 'yes' and oampsargs.has_key('port') is not None:
                if slot.has_key('password'):
                    gtvingamecommands.extend(gtv_reconnect(oampsargs['port'], password=slot['password']))
                else:
                    gtvingamecommands.extend(gtv_reconnect(oampsargs['port']))
            elif parameter == 'gtv' and value == 'no': # else we disconnect gtv so that it does not try to reconnect every few seconds uselessly (since gtv is disabled), because without the password it can't reconnect anyway
                for i in range(0,12):
                    gtvingamecommands.append('gtv_disconnect') # disconnect all games (12 should be enough)
            elif parameter == 'gtvrestart_hard':
                # A hard restart will completely shutdown the server and restart it with the given arguments (this is necessary to change mod)
                gtvparams['restart'] = ''
            elif 'gtvrepeat' in parameter and len(parameter) > len('gtvrepeat'):
                # Multiple GTV repeat: gtvrepeatx with x the number of consecutive resending of the same command to a GTV server (eg: gtvrepeat2)
                gtvcmdrepeat = int(parameter.replace('gtvrepeat', ''))
            # gtv exec = ingame commands for gtv
            elif parameter == 'gtvexec':
                gtvingamecommands.append(value)
            # special case: if this is a gtv command (except gtvexec that must be treated separately, and before), we put it in the gtvparams dictionnary
            # note: this must be last for gtv commands or else it will interfere with other special cases
            elif 'gtv' in str(parameter) or 'heartbeat' in str(parameter):
                gtvparams[str(parameter)] = value

            # Private event: if it's private, we disable recording facilities
            elif 'show_public' in str(parameter):
                if value == 'no':
                    ingamecommands.append('set sv_autoDemo 0')
                else:
                    ingamecommands.append('set sv_autoDemo 1')


            # Other ingame parameters (for standard use of the game rotator, like to change maps, mods, etc...)
            elif parameter == 'map':
                ingamecommands.append('map "'+value+'"')
            # If we pass in the --exec argument, we must put it in the ingamecommands array
            elif parameter == 'exec':
                ingamecommands.append(value)
            # special case: if verbose, this should be applied to all commands: for game server and gtv server
            elif parameter == 'verbose':
                oampsparams[str(parameter)] = value
                gtvparams[str(parameter)] = value

            # useless parameters (could be just ignored because oamps.sh will ignore them anyway, but it's cleaner to remove them)
            elif parameter == 'clan':
                None;

            # General oamps parameters parser
            # any other non special parameter in a slot will simply be taken as a commandline argument for oamps (this allows for specific behaviors depending on the mod, like setting the vm, homepath, basepath, etc.)
            else:
                oampsparams[str(parameter)] = value
            #else: # in any other case than specific to booking a server, we add them to ingamecommands and will be executed directly as in-game q3 commands (be careful to not put here too many for one slot, else it can overflow!)
            #    ingamecommands.append('seta '+str(parameter)+' "'+value+'"')


    #-- Build the final commands strings

    # Countdown management: if a countdown is specified but we are not going to restart (soft or hard) the server, then we should not notice the players with a countdown
    if oampsparams.has_key('countdown') and not ('map_restart' in ingamecommands or oampsparams.has_key('restart') or startup):
        del oampsparams['countdown']
    elif oampsparams.has_key('countdown') and startup: # in the case it's the first time we launch this script, we probably want to restart the server fresh ASAP. FIXME: if you want the server to restart after a countdown at startup, then remove this condition
        del oampsparams['countdown']


    # Special case: we change binary, so we have to relaunch the server in any case (but only if it changed since the last slot)
    if not oampsparams.has_key('binfullpath'):
        binfullpath = ''
    else:
        binfullpath = oampsparams['binfullpath']
    if last_binfullpath is not None and last_binfullpath != binfullpath: # we use a lot of short-circuits operators here (every and/or is a short-circuit operator in Python, meaning that if one condition is false it stops the evaluation of the condition right now)
        oampsparams['restart'] = '' # force the restart (to change binary)
        last_binfullpath = binfullpath # update the last bin (because after the restart we will be using that binary)
    if not oampsargs.has_key('restart_soft') and not defaultmod: last_binfullpath = binfullpath # only restart if we are not doing a soft restart and we haven't set a defaultmod (so by default we keep the last mod and config played)

    if not gtvparams.has_key('gtvfullpath'):
        gtvfullpath = ''
    else:
        gtvfullpath = gtvparams['gtvfullpath']
    if last_gtvfullpath is not None and last_gtvfullpath != gtvfullpath:
        gtvparams['restart'] = ''
        last_gtvfullpath = gtvfullpath
    if not oampsargs.has_key('restart_soft') and not defaultmod: last_gtvfullpath = gtvfullpath

    # Main command: oamps commandline arguments (other than ingame commands -e)
    for parameter, value in oampsparams.iteritems():
        if value is not None and value != '':
            command += ' --' + parameter + ' "' + value + '"'
        else:
            command += ' --' + parameter

    # Ingame commands: add to oamps commandline some ingame commands to execute
    # If we have some q3 ingame commands to execute directly in the console (ingamecommands), we add them in our main command var
    if ingamecommands != []:
        if oampsparams.has_key('restart') or startup: ingamecommands.append('map_restart') # restarting the map for the changes to take effect (only if the booking changed, if not we don't want the map to be restarted each slot even if it's the same booking! that's why do if it's hard or soft restarting the server)
        command +=  ' -e \'' + ';'.join(ingamecommands) + '\'' # we can use a single quote when passing arguments in bash shell, but this does not work in OA, only double quotes work, so using single quotes in commandline permits to escape double quotes in OA ingame commands
        if not oampsparams.has_key('execdelay'): # by default, we set an execdelay of 30 (can be overriden by commandline or slot parameter)
            command += ' --execdelay ' + str(int(default_cmddelay))

    # GTV command(s): build the gtv command
    # Note: gtv commands were separated for a reason of modularity and stability: we may want to only hard restart the game server to change the mod, not the gtv server because it may produce a bug
    # Note2: we only send gtv commands when the game server is restarted (soft or hard), meaning there's a change of booking. If that's not the case, this means that a booking is already running, and we should NOT disconnect and reconnect GTV during the match.
    if len(gtvparams) and (oampsparams.has_key('restart') or startup or gtvparams.has_key('restart') or (slot and slot.has_key('restart_soft'))):
        # Main GTV command
        for parameter, value in gtvparams.iteritems():
            if value is not None and value != '':
                gtvcommand += ' --' + parameter + ' "' + value + '"'
            else:
                gtvcommand += ' --' + parameter

        # GTV ingame commands: allows to reconnect to a booking where gtv is enabled (and to pass any ingame command to the gtv server)
        if gtvingamecommands != []:
            gtvcommand +=  ' --gtvexec \'' + ';'.join(gtvingamecommands) + '\''
            if not gtvparams.has_key('gtvexecdelay'): # by default, we set an execdelay of 60 for gtv (can be overriden by commandline or slot parameter)
                gtvcommand += ' --gtvexecdelay ' + str(int(default_gtvcmddelay))
    else: # else, if there's no gtvparams (the admin using oa-game-rotator has no gtv server), then this means that gtv is totally disabled, so we empty the gtvcommand so that no gtvcommand is issued (not really necessary but this spare one shell command and a few CPU cycles)
        gtvcommand = ''

    # is used to append -r at startup, then the next iterations will do as the slotsfile require
    if startup:
        command += ' -r'
        if gtvcommand != '': gtvcommand += ' -r'

    # Managing multiple consecutive restarts (useful for AfterShock)
    finalcmd = []

    if cmdrepeat > 0:
        finalcmd.extend([command]) # we put at least one command as is, with all options
        if oampsparams.has_key('countdown'): # if a countdown is set, we apply it only for the first command, for all the ones that follow, we don't use a countdown (eg: for aftershock servers that need to restarted twice, we don't want to restart it an hour later because of the countdown! the server must be restarted in a chain so that it's playable)
            command = re.sub('''--countdown ['"]*[\d]+['"]*''', '', command)
        finalcmd.extend([command] * (cmdrepeat-1)) # we repeat the command as many times as necessary

    if gtvcmdrepeat > 0:
        finalcmd.extend([gtvcommand])
        if gtvparams.has_key('countdown'):
            gtvcommand = re.sub('''--countdown ['"]*[\d]+['"]*''', '', gtvcommand)
        finalcmd.extend([gtvcommand] * (gtvcmdrepeat-1))

    return finalcmd






#***********************************
#                       MAIN
#***********************************

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    #==== COMMANDLINE PARSER ====

    #== General vars
    delimiter = '|' # for slots files
    timedelimiter = ':'
    assign = '='
    defaultwait = 5 # default wait time (in minutes) to wait when there's no slotsfile for today before checking again for a new slotsfile existence
    margindelay = 120 # seconds to wait after the planned end time of a booking to switch to the next (this allows players to take the time to end the match) - this margindelay is not applied when there's no booking, the next booking will begin right on time

    desc = '''OpenArena Game Rotator by GrosBedo ---
    Description: Reads a slots file and process all the commands for each slot at the corresponding time of the day. This can be used to schedule complex rotations with mods and settings changing, which is not possible otherwise.
    This application is designed to manage one game server and one gtv server per instance of the script. Use oa-booking-manager companion application to generate those slots files or look at an example to make one manually.
    '''
    ep = '''Note: You need oamps.sh to use this script, and you can here use almost all oamps.sh argument (NOTE: use only long-form, eg: --screenname), at commandline and/or in slotsfiles (parameters in slotsfiles override commandline).
    Last note: Do NOT use --addcron or -a in commandline, or else you may get some very weird results and a corrupted cron file!'''

    #== Commandline arguments
    #-- Constructing the parsers
    parent_parser = argparse.ArgumentParser(description=desc, epilog=ep,
                                     add_help=False, argument_default=argparse.SUPPRESS, conflict_handler="resolve")
    #slots_parser = parent_parser.add_argument_group('Slots_parser')
    #oamps_parser = parent_parser.add_argument_group('Oamps_parser')
    slots_parser = argparse.ArgumentParser(parents=[parent_parser], add_help=True, description=desc, epilog=ep)
    oamps_parser = argparse.ArgumentParser(parents=[parent_parser], add_help=True)
    # Slots management arguments
    slots_parser.add_argument('-x', '--server-name', metavar='somename', type=str, nargs=1, required=True,
                        help='Name of the server to watch for bookings (will be used to find the filename of the slotsfiles).')
    slots_parser.add_argument('-f', '--slots-folder', metavar='/some/folder/ (relative or absolute path)', type=is_dir, nargs=1, required=True,
                        help='Folder that contains the slotsfiles - if remote download is enabled, this is where the slotsfile will be downloaded. Note: please enable write access on this folder.')
    slots_parser.add_argument('-c', '--default-config', metavar='/some/folder/someconf.cfg (only relative path to game folder)', type=str, nargs=1, required=True, #type=argparse.FileType('rt')
                        help='Default config that will be loaded when there\'s no booking for the day.')
    slots_parser.add_argument('-g', '--default-gamemod', type=str, nargs=1, required=False, #default=None but we could set default=['baseoa'] for OpenArena
                        help='Default mod that will be loaded when there\'s no booking for the day. Note: If empty (default), the last gamemod loaded for the last booking will be kept, until next booking.')
    slots_parser.add_argument('-d', '--download-url', metavar='http://some.url/booking-download.php', type=str, nargs=1, required=False,
                        help='Enable remote download of bookings: URL to fetch the slotsfiles.')
    slots_parser.add_argument('-dp', '--download-password', metavar='somepassword', type=str, nargs=1, required=False,
                        help='Password for remote download (will be passed as $_GET parameter).')
    slots_parser.add_argument('--outputlogrotator', metavar='/some/file.txt', type=str, nargs=1, required=False,
                        help='Redirect all outputs to a log file.')
    slots_parser.add_argument('--margin-delay', metavar='seconds', type=int, nargs=1, required=False,
                        help='Seconds to wait after the planned end time of a booking to switch to the next (this allows players to take the time to end the match). Note: not applied when there\'s no booking, the next booking will begin right on time. Default: 2 minutes.')
    slots_parser.add_argument('-op', '--oampsfullpath', metavar='/some/path/oamps.sh', type=str, nargs=1, required=False,
                        help='Fullpath to oamps.sh script, including the script filename (default: same folder as the oa-game-rotator.py)')
    # OAMPS arguments
    # no addcron support! be careful, it will cause weird stuffs to happen (every slot will be registered in cron!)
    oamps_parser.add_argument('-b', '--basepath', metavar='/some/path', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-bin', '--binfullpath', metavar='/some/path', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('--countdown', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('--countdownmessage', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-e', '--exec', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-ec', '--execconfig', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-ed', '--execdelay', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-ext', '--extend', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-gb', '--gamebasemod', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('--homepath', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('--heartbeat', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('--heartbeatscreen', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('--heartbeattime', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-k', '--killall', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-k2', '--killall2', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-j', '--junk', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-l', '--log', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-lm', '--logmaxsize', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-lof', '--logoutputfolder', type=is_dir, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-m', '--multiple', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-n', '--number', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-o', '--outputlog', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-p', '--port', type=str, nargs=1, required=False,
                        help='see oamps help')
    #oamps_parser.add_argument('-r', '--restart', action='store_true', required=False,
    #                    help='see oamps help')
    oamps_parser.add_argument('-s', '--screenname', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-s2', '--screenname2', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tv', '--gtv', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvb', '--gtvbasepath', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvc', '--gtvconfig', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tve', '--gtvexec', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvec', '--gtvexecconfig', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tved', '--gtvexecdelay', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvh', '--gtvhomepath', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvm', '--gtvmaster', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvmp', '--gtvmasterport', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvmd', '--gtvmasterdelay', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvp', '--gtvport', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvs', '--gtvscreenname', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-tvbin', '--gtvfullpath', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-v', '--verbose', action='store_true', required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-vm', '--vmgame', type=str, nargs=1, required=False,
                        help='see oamps help')
    oamps_parser.add_argument('-w', '--watch', type=str, nargs=1, required=False,
                        help='see oamps help')


    #===== INITIALIZE VARIABLES ====

    #== Global variables
    startup = True # is used to force restart of the server at startup (by appending --restart and avoid the countdown), then the next iterations will do as the slotsfile require

    #== Parsing the arguments
    [args, rest] = slots_parser.parse_known_args(argv) # Storing all arguments to args
    [oampsargsraw, rest] = oamps_parser.parse_known_args(rest)

    oampsargs = oampsargsraw.__dict__ # Convert raw arguments (which is an object, and arguments being the object's fields) to a dictionary (because the function make_oamps_command takes only a dictionary as input to be able to iterate through each argument)

    #-- Set variables from arguments
    servername = args.server_name[0]
    slotsfolder = fullpath(args.slots_folder[0])
    defaultconf = os.path.basename(fullpath(args.default_config[0])) # Take only the filename. Can't take the full path here because it must be relative to the game server (the game engine can't exec absolute paths)

    if args.margin_delay: # Override the margin delay if specified at commandline
        margindelay = args.margin_delay[0]

    if oampsargs.has_key('countdown') and oampsargs['countdown'] and oampsargs['countdown'] != False:
        countdown = int(oampsargs['countdown'][0])
        margindelay = margindelay - countdown # adjusting margindelay with the countdown (we must launch the commands earlier because the countdown will delay a lot the effective beginning of the next booking)
    else:
        countdown = None

    if oampsargs.has_key('addcron'): # Security to avoid addcron which may corrupts the cron job file
        del oampsargs['addcron']
    if oampsargs.has_key('a'):
        del oampsargs['a']

    if args.outputlogrotator:
        sys.stdout = Tee(args.outputlogrotator[0], 'a')
        sys.stderr = Tee(args.outputlogrotator[0], 'a')

    if args.default_gamemod: # default mod if the slot is not booked or no slotsfile found for today
        defaultmod = args.default_gamemod[0] # if specified at commandline, we set the default gamemod to the one specified
    else:
        defaultmod = None # by default, we keep the same gamemod that was loaded for the last booking, until specified otherwise by a later booking

    oampsfullpath = None
    if args.oampsfullpath: # since we get the params and values from argparse, it has the bad habit of always creating a list for values even if it's a single value, so here if that's the case, we fetch the single value inside the list
        oampsfullpath = args.oampsfullpath[0]

    #===== MAIN LOOP ====
    # loop indefinitely
    while 1:

        #== Get today/now datetime and slotsfilename
        # Note: we must do it in the loop, because it can happen that we have no slot file for today and we wait for a new slotfile until the next day. In this case, we must update the date.
        [d, today, currtime] = get_today() # get today's date and time
        todayslotsfilepath = get_slotsfilename(today, slotsfolder, servername) # get today's slotsfile path

        #== Downloading slots file (if remote adress and password was specified in arguments)
        if (args.download_url and args.download_password):
            download_slotsfile(slotsfolder, servername, today, args.download_url[0], args.download_password[0])

        #== Read slots and nbslots from slots file
        r = read_slotsfile(slotsfolder, servername, delimiter, assign)

        #-- Loading default config if there's no slots file
        if r is None:
            print('No slots file could be found for today, the month, the year or even just the server. Loading the default config.')
            commands = make_oamps_command(defaultconf, defaultmod, oampsargs, None, startup, oampsfullpath)
            startup = False # set to false so that we don't restart automatically the next servers (unless required by the slotsfile)
            #-- Execute the commands
            for command in commands:
                if command is not None:
                    if oampsargs['verbose']:
                        print(command)
                    os.system(command)

            print('Waiting ' + str(defaultwait) + ' minutes before checking again if a slotfile exists.')
            if countdown: # If there's a countdown, we must launch commands earlier in case the next slot is booked, so that we don't begin the next booking too late
                slotwait(int(24*60/int(defaultwait)), timedelimiter, -countdown) # we wait using the slotwait function so that we synchronize with the time (if we use time.sleep(), we may miss the beginning of a slot, when with slotwait we have much less chances)
            else: # Else no countdown, we just launch the commands right on time
                slotwait(int(24*60/int(defaultwait)), timedelimiter)
        #-- Loading the slots list if a slots file is found
        else:
            [nbslots, slots] = r # assigning total number of slots and slots list

            #lastslot = -1 # memorize the last slot, so that we don't issue twice the same commands to the server (and so that we know when we must redownload the new slotsfile if we change day)

            #== SECOND MAIN LOOP ==

            # loop until nextslot belongs to the next day (when nextslot = 0)
            [currslot, nextslot, nexttime, nexttimestr, sleeptime] = get_slots_time_infos(nbslots, timedelimiter, margindelay)

            # While we are today (we loop until the very last slot, the next slot being 0 since it belongs to the next day slotsfile)
            while 1:
                #-- Get slots infos
                [currslot, nextslot, nexttime, nexttimestr, sleeptime] = get_slots_time_infos(nbslots, timedelimiter, margindelay)

                #-- Get the commands for the current slot
                commands = make_oamps_command(defaultconf, defaultmod, oampsargs, slots[currslot], startup, oampsfullpath)
                startup = False # set to false so that we don't restart automatically the next servers (unless required by the slotsfile)

                #-- Execute the commands
                for command in commands:
                    if command is not None:
                        if oampsargs['verbose']:
                            print(command)
                        os.system(command)

                #-- Wait for the next slot
                slotwait(nbslots, timedelimiter, margindelay)

                #-- Break loop if we day changed (we loop until the very last slot, the next slot being 0 since it belongs to the next day slotsfile)
                if currslot > nextslot: break # quick fix: if we launch the game rotator at the last slot of the day (eg: between 23:30 and 00:00 if there are 48 slots), we get an infinite loop of downloading the slots file until the next slot. Here we force to do the while and check only here at the end of the block to break and to download the new day's slotsfile.


# Calling main function if the script is directly called (not imported as a library in another program)
if __name__ == "__main__":
    sys.exit(main())
