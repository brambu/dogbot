#!/usr/bin/env python

import socket
import sys
import os
import string
import yaml
import re
import random
from time import sleep, time
from pprint import pprint as pp
from subprocess import Popen, PIPE
import xmlrpclib
from threading import Thread
from Queue import Queue
import logging
from argparse import ArgumentParser

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

class DogBot(object):
    
    def __init__(self, configfile, verbose):
        self.configfile = configfile
        self.configdict = self.readconfig(self.configfile)
        self.verbose = verbose
        self.inq = Queue(10000)
        self.outq = Queue(10000)
        self.runthreads = []
        self.threadlimit = 25
        self.altnick = False
        self.altnickcounter = 0
        self.lastnickchange = time()
        self.currentnick = None
        masterregex = r'(?:^:([^\s]+)\s([^\s]+)\s([^\s]+)\s([^:\s]+)?\s?:(.*))|(?:^(\w+))'
        self.lineregex = re.compile(masterregex)
        senderregex = r'(.*)!(.*)@(.*)'
        self.sregex = re.compile(senderregex)
        self.log = self.initlog()
    
    def initlog(self):
        log = logging.getLogger(__name__)
        return log
    
    def readconfig(self, configfile):
        configdict = {}
        try:
            openconfig = open(configfile, "r")
            configdata = openconfig.read()
            openconfig.close()
        except:
            raise RuntimeError("Could not open %s " % (configfile))
        try:
            configdict = yaml.load(configdata)
        except:
            raise RuntimeError("Could not parse %s" % (configfile))
        return configdict
    
    def help(self, sendto, helpquery=False):
        if helpquery == []:
            helpquery = False
        else:
            helpquery = helpquery[0]
        out      = []
        src      = self.currentnick
        cmddict  = self.configdict['cmds']
        chancmds = cmddict['chan'].keys()
        privcmds = cmddict['priv'].keys()
        out.append(" *  %s help:" % (src))
        if not helpquery:  
            helpprompt = [ 'Type "help nameofcommand" in order to', \
                           'display the help for that command', \
                           '', \
                           'Available commands are:']
            for line in helpprompt:
                out.append(" *  %s" % (line))
            cmdprompt = []
            cmdprompt.append('In channel commands:')
            for group in [chancmds[i:i+4] for i in range(0, len(chancmds), 4)]:
                cmdprompt.append(', '.join(group))
            cmdprompt.append('Private message only commands:')
            for group in [privcmds[i:i+4] for i in range(0, len(privcmds), 4)]:
                cmdprompt.append(', '.join(group))
            for line in cmdprompt:
                out.append(" *  %s" % (line))
        else:
            if helpquery in chancmds:
                helpprompt = [ '', \
                               'Help for in-channel command: %s' % (helpquery), \
                               cmddict['chan'][helpquery]['help'], \
                               '' ]
                for line in helpprompt:
                    out.append(" *  %s" % (line))
            elif helpquery in privcmds:
                helpprompt = [ '',
                               'Help for private msg command: %s' % (helpquery), \
                               cmddict['priv'][helpquery]['help'], \
                               '' ]
                for line in helpprompt:
                    out.append(" *  %s" % (line))
            else:
                out.append(" *  No one taught me that trick yet.. ")   
        self.saythis(out, src, sendto, limiter=False)
    
    def connect(self):
        host       = self.configdict['host']
        port       = self.configdict['port']
        realname   = self.configdict['realname']
        ident      = self.configdict['ident']
        nick       = self.configdict['nick']
        connectcmd = (host,port)
        self.s = socket.socket()
        self.s.connect(connectcmd)
        self.nickchange(nick)
        self.ident(ident, host, realname)
    
    def nickchange(self, nick):
        nickcmd = 'NICK %s\r\n' % (nick)
        self.s.send(nickcmd)
        self.currentnick = nick
        self.lastnickchange = time()
        self.log.info("Bot nick is now: %s" % (self.currentnick))
        sleep(2)
    
    def ident(self, ident, host, realname):
        identcmd = 'USER %s %s bla :%s\r\n' % (ident,host,realname)
        self.s.send(identcmd)
    
    def run(self):
        threads = []
        tr = Thread(target = self.runloop)
        ti = Thread(target = self.inloop)
        to = Thread(target = self.outloop)
        for t in [ti,to,tr]:
            t.daemon = True
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
    
    def runloop(self):
        while True:
            try:
                line = self.inq.get()
                if self.verbose:
                    self.log.info(line)
                self.lineparse(line)
            except Exception, e:
                self.log.fatal(e)
                os._exit(1)
    
    def inloop(self):
        while True:
            try:
                lines = self.s.recv(2048)
                for line in lines.split('\r\n'):
                    if not line=='':
                        self.inq.put(line)
            except Exception, e:
                self.log.error(e)
                continue
    
    def outloop(self):
        while True:
            try:
                i = self.outq.get()
                self.s.send(i)
            except Exception, e:
                self.log.error(e)
                continue
    
    def lineparse(self, line):
        matches = self.lineregex.findall(line)
        if matches:
            match = matches[0]
            if len(match) > 5:
                sender = match[0]
                action = match[1]
                recip  = match[2]
                victim = match[3]
                msg    = match[4]
                extra  = match[5]
                nick   = sender
                ident  = ""
                host   = ""
                if '!' in sender:
                    smatches = self.sregex.findall(sender)
                    if smatches:
                        smatch = smatches[0]
                        if len(smatch) > 2:
                            nick  = smatch[0]
                            ident = smatch[1]
                            host  = smatch[2]
                if action == '001': #welcome
                    self.log.info("Welcome message detected, joining channels.")
                    self.autojoiner()
                if action == '433': #nick is in use
                    if self.currentnick == self.configdict['altnick']:
                        self.log.warn("Both nick and alt in use...Sleeping for 10s")
                        sleep(10)
                        nick = self.configdict['nick']
                        self.log.warn("Trying primary..")
                        self.nickchange(nick)
                        return
                    self.altnick = True
                    nick = self.configdict['altnick']
                    self.log.warn("Nick in use, using alternate: %s" % (nick))
                    self.nickchange(nick)
                if self.altnick:
                    self.altnickcounter+=1
                    if self.altnickcounter > 20:
                        nick = self.configdict['nick']
                        self.log.info("Trying to revert to original nick: %s" % (nick))
                        self.nickchange(nick)
                        self.altnick = False
                        self.altnickcounter = 0
                if not extra == '':
                    if extra == 'PING':
                        self.pong(line)
                    if extra == 'ERROR':
                        self.reconnect()
                if action == 'PRIVMSG':
                    self.privmsgparse(nick, ident, host, recip, msg)
                if action == 'KICK':
                    self.kickrejoin(nick, victim, recip)
                if action == 'INVITE':
                    if recip == self.currentnick:
                        if nick in self.configdict['admins']:
                            channel = msg
                            self.invitejoin(nick, channel)
    
    def privmsgparse(self, nick, ident, host, recip, msg):
        if '#' in recip:
            privmsg = False
        elif recip == self.currentnick:
            privmsg = True
        else:
            return
        if privmsg:
            cmd = msg.split()[0]
            args = msg.split()[1::]
            self.run_cmd(cmd, args, nick, recip, 'priv')
        else:
            if msg.split(':')[0] == self.currentnick:
                try:
                    completecmd = msg.split(':')[1::]
                    cmd = completecmd[0].split()[0].strip()
                    args = completecmd[0].split()[1::]
                    self.run_cmd(cmd, args, nick, recip, 'chan')
                except Exception, e:
                    self.log.error(e)
                    pass
        return
    
    def kickrejoin(self, kicker, victim, channel):
        self.log.info("kick detected {0} {1} {2}".format(kicker, victim, channel))
        if not victim == self.currentnick:
            self.log.info("{0} is not {1}".format(victim, self.currentnick))
            return
        self.log.info("%s kicked %s from %s" % (kicker, self.currentnick, channel))
        channelkey = ""
        if channel in self.configdict['channels']:
            if 'key' in self.configdict['channels'][channel]:
                channelkey = self.configdict['channels'][channel]['key']
            self.join(channel, channelkey)
        return
    
    def invitejoin(self, nick, channel):
        self.log.info("%s invited %s to %s" % (nick, self.currentnick, channel))
        self.join(channel)
        return
    
    def reconnect(self):
        self.log.warn("ERROR detected, reconnecting after 10 sec.")
        self.s.close()
        sleep(10)
        self.connect()
        self.autojoiner()
        return
    
    def pong(self, line):
        pongcmd = 'PONG %s\r\n' % (line.split()[1])
        self.log.info("%s <-> %s" % (line.strip(), pongcmd.strip()))
        self.s.send(pongcmd)
        return
    
    def autojoiner(self):
        channels = self.configdict['channels']
        for channel in channels.keys():
            if 'key' in channels[channel]:
                channelkey = channels[channel]['key']
            else:
                channelkey = ''
            self.join(channel, channelkey)
        return
    
    def join(self, channel, key=''):
        joincmd = 'JOIN %s %s\r\n' % (channel, key)
        self.log.info('Joining %s' % (channel))
        self.s.send(joincmd)
        return
    
    def run_cmd(self, cmd, args, sender, recip, cmdtype):
        self.runthreads = [thread for thread in self.runthreads if thread.is_alive()]
        if len(self.runthreads) > self.threadlimit:
            if len(self.runthreads) > self.threadlimit:
                log.warn("Dropping cmd %s from %s due to too many alive threads." % (cmd, sender))
                sendto = sender
                if cmdtype=='chan':
                    sendto = recip
                out = ['I feel like throwing up... :( ..Try again later.']
                self.saythis(out, self.currentnick, sendto)
                return
        else:
            t = Thread(target=self._run_cmd_tjob, args=(cmd, args, sender, recip, cmdtype, ))
            t.daemon = True
            t.start()
            self.runthreads.append(t)
        
    def _run_cmd_tjob(self, cmd, args, sender, recip, cmdtype):
        self.log.info("%s@%s is running cmd: '%s' with args %s" % (sender, recip, cmd, args)) 
        out = []
        cmddict = self.configdict['cmds']
        src = self.currentnick
        saneargs = []
        validcmds = []
        cleanregex = r'[^A-Za-z0-9\-\.]'
        validcmds.extend(cmddict['chan'].keys())
        sendto = recip
        limiter = True
        if cmdtype=='priv':
            sendto = sender
            limiter = False
            validcmds.extend(cmddict['priv'].keys())
        if cmd == 'help':
            sendto = sender
            self.help(sendto, args)
            return
        elif cmd == 'reload-config':
            if sender in self.configdict['admins']:
                self.log.info("%s is in %s and is issuing a config reload" % (sender, ','.join(self.configdict['admins'])))
                self.configdict = self.readconfig(self.configfile)
            else:
                self.log.warn("%s is not authorized to reload configs." % (sender))
        elif cmd in validcmds:
            for arg in args:
                sanearg = re.sub(cleanregex, '', arg)
                saneargs.append(sanearg)
            try:
                if cmdtype=='priv':
                    if cmd in cmddict['chan']:
                        cmdtype='chan'
                if cmddict[cmdtype][cmd]['acl']:
                    if sender not in self.configdict['admins']:
                        self.log.warn("%s is not authorized." % (sender))
                        cmd = '_%s_' % (cmd)
                shell_command = cmddict[cmdtype][cmd]['cmd']
                shell_args = " ".join(saneargs)
                out = self.__shellCall("%s %s" % (shell_command, shell_args))
            except:
                out.append(self.snark(cmd))
        else:
            out.append(self.snark(cmd))
        self.saythis(out, src, sendto, limiter)
        return
    
    def saythis(self, outlist, src, sendto, limiter=True):
        out = []
        if outlist == ['']:
            out.append("There is nothing...")
        elif len(outlist) > 4:
            if limiter:
                out.append("Result too long.")
            else:
                out = outlist
        else:
            out = outlist
        for line in out:
            self.outq.put_nowait(':%s PRIVMSG %s :%s\r\n' % (src, sendto, line))
            if limiter:
                sleep(0.2)
        return
        
    def __shellCall(self, command):
        p = Popen(
        command,
        stderr=PIPE,
        stdout=PIPE,
        close_fds=True, 
        shell=True)
        out, err = p.communicate()
        if err:
            self.log.warn(err)
        return out.splitlines()
    
    def snark(self, cmd):
        snarks = ['\x02%s\x02? Having fun, hacker?',\
                  '\x02%s\x02? This is just wasting time...',\
                  '\x02%s\x02? Have you tried "help"?',\
                  '\x02%s\x02? I am not having fun anymore.',\
                  '\x02%s\x02? I am warning you.',\
                  '\x02%s\x02? Can I ban?',\
                  '\x02%s\x02? Can I kick?',\
                  '\x02%s\x02? English?',\
                  '\x02%s\x02??????????????????????? whuuu?',\
                  '\x02%s\x02? Why is a raven like a writing desk?',\
                  '\x02%s\x02? Are you using a typewriter?',\
                  '\x02%s\x02? Well.... I never...',\
                  '\x02%s\x02? Violation!',\
                  'Hey, click this: http://lmgtfy.com/?q=%s',\
                  'Do people laugh when you say \x02%s\x02 normally?',\
                  'If I knew how to \x02%s\x02 I wouldn\'t be a bot.']
        maxindex = len(snarks) - 1
        snark = snarks[random.randint(1,maxindex)]
        snark = snark % cmd
        return snark

def main():
    
    parser = ArgumentParser(description='An irc bot.')
    parser.add_argument('-v', '--verbose', \
                        action = 'store_true', help = 'Be verbose.', default=False )
    parser.add_argument('-C', '--config', \
                        required = True, help = 'Config file')
    
    args = parser.parse_args()
    
    verbose = args.verbose
    configfile = args.config
    bot = DogBot(configfile, verbose)
    bot.connect()
    bot.run()

if __name__ == '__main__':
    sys.exit(main())
