#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aidsbot import aidsbot
from time import *
from code import interact

config = {}
msg_counter = {'current_talker': None, 'flood': 0, 'old_time': time()}

def parse_config(conf_file = "monologue.conf"):
    f = open(conf_file, "r")
    for line in f:
        if not '#' in line.split('=')[0]:
            if ',' in line.split('=')[1]:
                config[line.split('=')[0].rstrip().lstrip()] = line.split('=')[1].rstrip().lstrip().split(',')
            elif unicode(line.split('=')[1]).isnumeric():
                config[line.split('=')[0].rstrip().lstrip()] = int(line.split('=')[1].rstrip().lstrip())
            else:
                config[line.split('=')[0].rstrip().lstrip()] = line.split('=')[1].rstrip().lstrip()
    
    if len(config) < 8:
        print "You have too few options in the config."
        exit(1)
    elif len(config) > 9:
        print "You have too many options in the config."
        exit(1)
    else:
        print "Config looks alright, let's continue"
                
    #for key, value in config.iteritems():
    #    print ("%s %s = %s %s" % (type(key), key, type(value), value))

def privmsg(irc,data):
    user_info, msg_type, channel, message = irc.privmsg_split(data)
    username, real_user, host = irc.user_split(user_info)
    current_time = time()
    #print "%s %s %s %s" % (type(username), username, type(msg_counter['current_talker']), msg_counter['current_talker'])

    if username != msg_counter['current_talker']:
        msg_counter['current_talker'] = username
        msg_counter[channel.lstrip('#')] = 1
        msg_counter['flood'] = 0
    else:
        msg_counter[channel.lstrip('#')] += 1
        diff = float(current_time) - float(msg_counter['old_time'])
        if diff < 2.6:
            msg_counter['flood'] += 1
        else:
            msg_counter['flood'] = 0
        #print "%s %s = %d flood: %d time taken: %s %f" % (msg_counter['current_talker'], channel.lstrip('#'), msg_counter[channel.lstrip('#')], msg_counter['flood'], type(diff), diff)
    
    if msg_counter['flood'] > int(config['flood_limit']):
        irc.kick(channel, msg_counter['current_talker'], config['flood_kick_msg'])
        msg_counter[channel.lstrip('#')] = 0
        msg_counter['flood'] = 0
    elif msg_counter[channel.lstrip('#')] > int(config['monologue_limit']):
        irc.kick(channel, msg_counter['current_talker'], config['monologue_kick_msg'])
        msg_counter[channel.lstrip('#')] = 0
        msg_counter['flood'] = 0
    msg_counter['old_time'] = current_time


def sources(irc, data):
    user_info, msg_type, channel, message = irc.privmsg_split(data)
    username, real_user, host = irc.user_split(user_info)
    irc.privmsg(channel, "%s: Sources for monologue can be found at: %s and sources for aidsbot can be found at: %s" % (username, "https://github.com/lejonet/Monologue", "https://github.com/adisbladis/aidsbot"))


parse_config()
irc = aidsbot(config['botname'], config['server'], int(config['port']), True) #Set up the object
irc.connect() #Actually connect
for channel in config['channels']:
    irc.join(channel) #Join a channel
    irc.privmsg(channel, 'Sir, Ready for duty, Sir!') #Send a message

irc.chanophandler_add("PRIVMSG", privmsg)
irc.privmsghandler_add("!source", sources)
irc.privmsg("NickServ", "IDENTIFY "+config['irc_password'])
irc.listen() #Start listening

while True:
    interact(local=locals()) #Important, will die otherwise
