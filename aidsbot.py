#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

aidsbot - A simple irc bot library for python
Copyright (C) 2011 Adam Hose <adisbladis@m68k.se>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import socket
import thread
import time
import threading

class aidsbot ():
    '''Handle IRC connections'''
    def __init__(self, botname, network, port, debug = False):
        self.network = network
        self.port    = port
        self.botname = botname
        self.debug   = debug
        self.run     = True
        self.privmsghandler = {}
        self.chanophandler  = {}
        self.chanlist= []
        self.failed  = False

    def connect(self):
        '''Connect'''
        self.socket = socket.socket()
        self.socket.connect((self.network, self.port))
        self.send("NICK %s" % (self.botname),True)
        self.send("USER %s %s bla :%s" % (self.botname, self.network, self.botname),True)
        try: self.postconnect(self)
        except: pass
        self.failed=False

    def join(self, channel, addlist=True):
        '''Join channel'''
        if addlist:
            self.chanlist.append(channel)
        return self.send("JOIN :%s" % channel)
    
    def privmsg(self, target, message):
        '''Send message to target'''
        return self.send("PRIVMSG %s :%s" % (target, message))

    def mode(self, user, mode, channel = ''):
        '''Change user/channel modes on target'''
        return self.send("MODE %s %s %s" % (channel, mode, user))
    
    def kick(self, channel, user, reason = None):
        '''Kick user from channel for reason'''
        return self.send("KICK %s %s :%s" % (channel, user, reason))
    
    
    def send(self, command, override=False):
        '''Send a raw command to the socket'''
        #Dont try to send if network has failed
        if not self.failed or override:
            self.socket.send("%s\r\n" % command)
        else:
            return None
    
    def stop(self):
        '''Stop'''
        self.run = False
        self.send('QUIT')
        self.socket.close()

    def privmsghandler_add(self,command,function):
        '''Add function as handler for trigger'''
        command = ":" + command
        self.privmsghandler[command]=function

    def chanophandler_add(self,chanop,function):
        '''Add function as handler for channel operation'''
        self.chanophandler[chanop]=function

    def privmsg_split(self,data):
        '''Split data for easy usage'''
        data = data.split()
        user_info = data[0]
        msg_type = data[1]
        channel = data[2]
        message = data[3]
        for i in range(4,len(data)):
            message = message + " " + data[i]
        return user_info, msg_type, channel, message        

    def user_split(self,data):
        '''Split the user-data'''
        nick, rest = data.split("!")
        nick=nick.replace(":","",1)
        real_user=rest.split("@")[0]
        host=rest.split("@")[1]
        return nick, real_user, host

    def listen(self):
        '''Start listener in thread'''
        thread.start_new_thread(self.listener, ())

    def listener(self):
        '''Listener, should be started from listen() instead'''
        while self.run:
            data = self.socket.recv(512)

            #Reply to ping :)
            if data.find('PING') != -1:
                self.send('PONG ' + data.split()[1] + "\r\n")

            #Handle user commands
            user_input = data.split()
            try:
                chanop = user_input[1]
            except IndexError:
                chanop = "FAIL" #Network failed

            #Check for trigger
            if chanop == "PRIVMSG":
                command = user_input[3]
                try:
                    thread.start_new_thread(self.privmsghandler[command], (self,data))
                except KeyError: pass #Unhandled
            elif chanop == "FAIL":
                #Reconnect if failure
                self.failed=True
                while self.failed:
                    time.sleep(5)
                    try:
                        self.connect()
                    except socket.error:
                        self.failed=True
                for chan in self.chanlist:
                    self.join(chan,False)

            #Always try chanop
            try: thread.start_new_thread(self.chanophandler[chanop], (self,data))
            except: pass #Unhandled

            #Debug messages
            if self.debug == True:
                print data
