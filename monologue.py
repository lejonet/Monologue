#!/usr/bin/env python

from aidsbot import aidsbot
import time
import code

config = {}
msg_counter = {}

def parse_config(conf_file = "monologue.conf"):
    f = open(conf_file, "r")
    for line in f:
        if not '#' in line.split('=')[0]:
            if ',' in line.split('=')[1]:
                config[line.split('=')[0].rstrip().lstrip()] = line.split('=')[1].rstrip().lstrip().split(',')
            else:
                config[line.split('=')[0].rstrip().lstrip()] = line.split('=')[1].rstrip().lstrip()

    for key, value in config.iteritems():
        print ("%s %s = %s %s" % (type(key), key, type(value), value))

def join(irc,data):
    '''Handle joins'''
    print "A user has joined"
    username, real_user, host = irc.user_split(data.split()[0])
    irc.privmsg(data.split()[2].lstrip(':'), "Greetings %s!" % (username))

def postconnect(irc):
    print "Postconnect function was triggered"
    #irc.privmsg("NickServ", "IDENTIFY "+config['ircpassword'])

def privmsg(irc,data):
    user_info, msg_type, channel, message = privmsg_split(data)
    username, real_user, host = user_split(user_info)

    if username != msg_counter['current_talker']:
        msg_counter['current_talker'] = username
        msg_counter[channel] = 1
        msg_counter['flood'] = 0
    else:
        msg_counter[channel] += 1
    print "%s %s = %d" % (msg_counter['current_talker'], channel, msg_counter[channel])

def sources(irc, data):
    user_info, msg_type, channel, message = privmsg_split(data)
    username, real_user, host = user_split(user_info)
    irc.privmsg("%s: Sources for monologue can be found at: %s", (username, "https://github.com/lejonet/Monologue"))
    irc.privmsg("%s: Sources for aidsbot can be found at: %s and sources for lejonet's fork of aidsbot can be found at: %s" % (username, "https://github.com/adisbladis/aidsbot", "https://github.com/lejonet/aidsbot"))


parse_config()
irc = aidsbot(config['botname'], config['server'], 6667, True) #Set up the object
irc.postconnect=postconnect
irc.connect() #Actually connect
for channel in config['channels']:
    irc.join(channel) #Join a channel
    irc.privmsg(channel, 'Yo maddafakas!') #Send a message

irc.chanophandler_add("JOIN",join)
irc.chanophandler_add("PRIVMSG", privmsg)
irc.privmsghandler_add("!source", sources)
irc.listen() #Start listening

while True:
    code.interact(local=locals()) #Important, will die otherwise
