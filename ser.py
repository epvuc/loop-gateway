#! /usr/bin/env python
# eric volpe 9/2016
# See README.TXT for info. 

import serial
import sys
import time
import shlex
import subprocess
import socket
import select
import os
import signal
from threading import Timer

LTRS = chr(0x1f)
FIGS = chr(0x1b)

# ascii/baudot maps and their inversions
ltrs = {0: 0, 1: 'E', 2: '\n', 3: 'A', 4: ' ', 5: 'S', 6: 'I', 7: 'U', 8: '\r', 9: 'D', 10: 'R', 11: 'J', 12: 'N', 13: 'F', 14: 'C', 15: 'K', 16: 'T', 17: 'Z', 18: 'L', 19: 'W', 20: 'H', 21: 'Y', 22: 'P', 23: 'Q', 24: 'O', 25: 'B', 26: 'G', 27: 0, 28: 'M', 29: 'X', 30: 'V'} 

figs = {0: 0, 1: '3', 2: '\n', 3: '-', 4: ' ', 5: '\x07', 6: '8', 7: '7', 8: '\r', 9: '$', 10: '4', 11: "'", 12: ',', 13: '!', 14: ':', 15: '(', 16: '5', 17: '"', 18: ')', 19: '2', 20: '#', 21: '6', 22: '0', 23: '1', 24: '9', 25: '?', 26: '&', 27: 0, 28: '.', 29: '/', 30: ';'}
srtl = {}
sgif = {}
for k, v in ltrs.iteritems():
    srtl[v] = k
for k, v in figs.iteritems():
    sgif[v] = k

# config options that should be in a config file, not here. 
wrap_output = 72
kick_sockets_on_break = False
feed_sockets = 'lines'
exec_timeout = 45
midline_timeout_secs = 60
control_power = False
control_power_timeout = 60 # how long to leave motor running before idle timeout

# macros for typing characters that don't exist in baudot
# TODO: macros and commands should be read from a config file, not hardcoded here. 
input_subs = [
    ('$POUND', '#'), ('$AT', '@'),    ('$US', '_'),   ('$PCT', '%'),
    ('$STAR', '*'),  ('$GT', '>'),    ('$GT', '>'),   ('$LT', '<'),
    ('$SC', ';'),    ('$PIPE', '|')
]

# commands to be run on tty input
cmds = { '$sms': { 'cmd': '/opt/ttycommands/send_sms_twilio.py', 'stdin': False, 'args': True } ,
         '$smsr': { 'cmd': '/opt/ttycommands/send_sms_flowroute.py', 'stdin': True, 'args': '1' },
         '$ping': { 'cmd': '/bin/echo Pong.\x07', 'stdin': False } ,
         '$exec': { 'cmd': '', 'shell': True, 'stdin': False, 'args': True } ,
         '$sexec': { 'cmd': '', 'shell': True, 'stdin': False, 'args': True, 'stdin': True } ,
         '$login': { 'cmd': '/bin/true', 'stdin': False, 'args': True },
         '$tweets': { 'cmd': '/opt/ttycommands/tweets.py', 'stdin': False, 'args': False },
         '$tweet': { 'cmd': '/opt/ttycommands/tweet', 'stdin': True, 'args': False },
         '$status': { 'cmd': '/opt/ttycommands/status.sh', 'stdin': False, 'args': False },
         '$uptime': { 'cmd': '/usr/bin/uptime', 'stdin': False, 'args': False },
         '$wx': { 'cmd': '/opt/ttycommands/grabweather.sh', 'stdin': False, 'args': '1' },
         '$feed': { 'cmd': '/opt/ttycommands/grabfeed.sh', 'stdin': False, 'args': False },
         '$haight': { 'cmd': '/opt/ttycommands/haighteration.sh', 'stdin': False, 'args': False },
         '$slack': { 'cmd': '/opt/ttycommands/slack.sh', 'args': '1' },
         '$lock': { 'cmd': '/opt/ttycommands/ttylock.sh' },
         '$unlock': { 'cmd': '/opt/ttycommands/ttyunlock.sh' },
         '$email': { 'cmd': '/opt/ttycommands/send_email.py', 'stdin': True, 'args': True },
         '$wpress': { 'cmd': '/opt/ttycommands/wpress.py', 'stdin': True, 'args': True },
         '$reddit': { 'cmd': '/opt/ttycommands/reddit.py', 'args': '1' },
         '$ttyon': { 'cmd': '/opt/ttycommands/tty-on', 'args': False },
         '$ttyoff': { 'cmd': '/opt/ttycommands/tty-off', 'args': False },
         '$reperfon': { 'cmd': '/opt/ttycommands/reperf-on', 'args': False },
         '$reperfoff': { 'cmd': '/opt/ttycommands/reperf-off', 'args': False },
         '$xmpp': { 'cmd': '/opt/ttycommands/xmpp.sh', 'stdin': False, 'args': '1' },
         '$tstream': { 'cmd': '/opt/ttycommands/tstream.sh', 'stdin': False, 'args': True },
         '$nostream': { 'cmd': '/usr/bin/pkill -f new-telestream.py', 'stdin': False, 'args': False },
         '$tsearch': { 'cmd': '/opt/ttycommands/tsearch.py', 'stdin': False, 'args': True },
         '$fortune': { 'cmd': '/usr/games/fortune', 'args': False },
}

# WHICH TYPE OF INTERFACE
# for usb-tty adapter in "NOTRANSLATE" mode. 
#ser = serial.Serial('/dev/ttyACM0', 300, timeout=2, xonxoff=False, rtscts=False, dsrdtr=False)

# for cp2102 dev board with optoisolators.
ser = serial.Serial('/dev/cp2102', 1200, timeout=2, xonxoff=False, rtscts=False, dsrdtr=False, bytesize=5, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO)

ser.flushInput()
starttime = time.time()
output = ''
input_append_mode = False
input_block = ''
run_as_shell = False

# commands that take an input block (instead of just command line args) 
# will be run here. 

def whine(p):
    print p

def process_block(b):
    global input_append_mode
    global input_block
    global commandlist
    global run_as_shell
    global output
    print "Processing input block for", commandlist
    print "Input is:", repr(input_block)
    if "$abort" in input_block.lower():
        print "Aborting process_block"
        input_append_mode = False
        input_block = ''
        line = ''
        output = 'aborted\r\n'
        return
    if run_as_shell:
        shellcmd = ' '.join(commandlist)
        print "Executing shell cmdline with stdin:", repr(shellcmd)
        p = subprocess.Popen(shellcmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    else:
        p = subprocess.Popen(commandlist, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    run_as_shell = False
    kill_proc = lambda x: os.killpg(os.getpgid(x.pid), signal.SIGTERM)
    # execute the command in a subprocess, and kill it if it takes too long
    timer = Timer(exec_timeout, kill_proc, [p])
    try:
        timer.start()
        result = p.communicate(input=input_block)
    finally:
        timer.cancel()
    print "exec ended with status", p.returncode, "result:", result
    if result[0]:
        output = result[0].replace('\n', '\r\n')
    else:
        #output = "no output\r\n"
        output = ""
    if p.returncode != 0:
        if p.returncode == -15:
            retcodestring = '(TIMED OUT)'
        else:
            retcodestring = '(ERROR %d)' % (p.returncode)
        if result[1]:
            output = output + '\r\n%s\r\n%s\r\n' % (retcodestring, result[1].replace('\n', '\r\n'))
        else:
            output = output + '\r\n%s\r\n' % (retcodestring)

    print "Trying to print message, ", repr(output)
    input_block = ''
    
# all input lines of text go through here, including ones that initiate a
# command execution. 

def process_line(l):
    # all these globals are gross.
    global output
    global input_append_mode
    global input_block
    global commandlist
    global run_as_shell
    global control_power
    global powerstate
    print "\nGot line: [%s]" % (l)

    # "$abort" anywhere in a line aborts both the current line and the 
    # current text block if we're currently in block input mode. 
    if "$abort" in l.lower():
        output="aborted\r\n"
        l = ''
	input_block=''
        input_append_mode = False
        return

    # if we're in the middle of inputting a block of text for a command,
    # append it to the input block and if we're done, feed it to process_block. 
    # The commandline to execute is in global var 'command' 
    if input_append_mode:
        if l.upper() == 'NNNN':
            input_append_mode = False
            process_block(input_block)
        else:
            input_block = input_block + l + '\r\n'
        print "returning from process_line after appending", l
        return 
        # this return means neither relaying to sockets nor interpreting commands
        # will happen while we're inputting a block of text. 

    # parse the incoming line to see if it's a command for us to run
    if l.startswith('$'):
        allargs = l.split()
        cmd = allargs[0].lower()
        print "checking", l, "as command", cmd
        # Special internal commands that don't work via exec. 
        if cmd == "$kick":
            for s in socklist:
                if s != listen_sock:
                    s.close()
                    socklist.remove(s)
            output = "all sockets closed\r\n"
            return
        if cmd == "$powerctl":
            if len(allargs) > 1:
                if allargs[1].lower() == "on":
                    print "Turning on power control."
                    control_power = True
                    powerstate = True # assume power is on since the cmd was typed.
                else:
                    if allargs[1].lower() == "off":
                        print "Turning off power control."
                        control_power = False

            if control_power:
                output = "power control is on.\r\n"
            else:
                output = "power control is off.\r\n"
            return
        # Look up the command in the list of command definitions and try to run it.
        if cmd in cmds:
            # if the command definition doesn't say to pass args, don't. 
            if ('args' not in cmds[cmd]) or (cmds[cmd]['args'] == False):
                print "this command gets no args"
                commandlist = cmds[cmd]['cmd'].split()
            else:
                # If 'args' field is True, pass all args
                print "this command gets all args"
                if cmds[cmd]['args'] == True:
                    commandlist = cmds[cmd]['cmd'].split() + allargs[1:]
                else:
                    # if 'args' field is a number, pass N args
                    nargs = int(cmds[cmd]['args'])+1
                    print "this command gets N args, nargs=", nargs
                    commandlist = cmds[cmd]['cmd'].split() + allargs[1:nargs]

            # if definition sets 'shell' true, concatenate all args into a string
            # and pass it to a shell to evaluate. dangerous, obviously. 
            if ('shell' in cmds[cmd]) and (cmds[cmd]['shell'] == True):
                run_as_shell = True
            print cmd, "matches", cmds[cmd], ", running it."
            print "command:", commandlist
            if 'stdin' in cmds[cmd] and cmds[cmd]['stdin']:
                print "This command wants stdin."
                # just turn on input append mode, exec will happen elsewhere when input is finished.
                input_append_mode = True
                if 'prompt' in cmds[cmd]:
                    output = cmds[cmd]['prompt']
            else:
                print "This command doesn't want stdin."
                # execute here, run under a timer so it can't hang.
                input_append_mode = False
                if run_as_shell == True:
                    shellcmd = ' '.join(commandlist)
                    print "Executing shell cmdline:", repr(shellcmd)
                    p = subprocess.Popen(shellcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
                else:
                    print "Executing cmd list", repr(commandlist)
                    p = subprocess.Popen(commandlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
                # because subprocesses might be spawned, we need to be sure to kill whole proc grp on timeout
                kill_proc = lambda x: os.killpg(os.getpgid(x.pid), signal.SIGTERM)
                run_as_shell = False
                timer = Timer(exec_timeout, kill_proc, [p])
                try:
                    timer.start()
                    result = p.communicate()
                finally:
                    timer.cancel()
                print "exec ended with status", p.returncode, "result:", result
                if result[0]:
                    output = result[0].replace('\n', '\r\n')
                else:
                    # output = "no output\r\n"
                    output = ""
                if p.returncode != 0:
                    if p.returncode == -15:
                        retcodestring = '(TIMED OUT)'
                    else:
                        retcodestring = '(ERROR %d)' % (p.returncode)
                    if result[1]:
                        output = output + '\r\n%s\r\n%s\r\n' % (retcodestring, result[1].replace('\n', '\r\n'))
                    else:
                        output = output + '\r\n%s\r\n' % (retcodestring)
        else:
            output = 'command not found.\r\n'
        return
        # This return means "$" commands will not be echoed to connected tcp sockets.

    if (feed_sockets == 'lines'): # and not input_append_mode:
        # character that just came in gets sent to all open tcp connections
        # unless we're typing an input block to a command.
        for s in socklist:
            if s != listen_sock:
                try:
                    print "sending", l, "to client at", s.getpeername()[0]
                    s.sendall(l + '\r\n')
                except:
                    print "Socket appeared to be dropped on send attempt, removing."
                    s.close()
                    socklist.remove(s)


shift = "LTRS"
asciiqueue = ''
downshift = False
line = ''
powerstate = True

# this sends out a single baudot character, with no translation.
# it returns True if it was sent successfully (char echoed back = char sent)
# or False if the char was mangled. 
# TODO: implement a timeout here as well.
def transmit_char(c):
    global output
    global last_tty_activity
    global control_power
    global powerstate
    # zero the tty idle time counter. 
    last_tty_activity = time.time()
    if control_power:
        if powerstate == False:
            power_on()
    ser.write(c)
    while(ser.inWaiting() == 0):
        time.sleep(0.001)
    got = ser.read(1)
    if got != c:
        print "Interrupted:", ord(got), "!=", ord(c), ", stopping print."
        output = ''
        time.sleep(0.5)
        ser.flushInput()
        return(False)
    else:
        return(True)

# general purpose line splitter to avoid overstriking
# have to be careful with cr/lf.
def linewrap(blob, width = 72):
    lines = blob.splitlines(True)
    new = []
    for l in lines:
        while True:
            if len(l) > width :
                new.append(l[:width] + '\r\n')
                l = l[width:]
                # if a space gets moved to the front of the next line, remove it
                if l[0] == ' ':
                    l = l[1:]
            else:
                new.append(l)
                break
    print "New:", repr(new)
    return ''.join(new)

def power_on():
    global powerstate
    print "===> Powering on at", time.ctime()
    on_cmd = ['/usr/bin/br', '-x', '/dev/x10transmitter', 'O1', 'on']
    try:
        p = subprocess.Popen(on_cmd)
        powerstate = True
    except:
        print "Exec power-on subprocess failed."
    time.sleep(4)

def power_off():
    global powerstate 
    print "===> Powering off at", time.ctime()
    on_cmd = ['/usr/bin/br', '-x', '/dev/x10transmitter', 'O1', 'off']
    try:
        p = subprocess.Popen(on_cmd)
        powerstate = False
    except:
        print "Exec power-off subprocess failed."
        
# set up TCP listener for network connections.
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_addr = ('0.0.0.0', 11123)
listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_sock.bind(listen_addr)
listen_sock.listen(1)
socklist = []
socklist.append(listen_sock)

chars_since_last_crlf = 0
last_tty_activity = time.time()

# Loop forever processing events. 
while True:
    idle = time.time() - last_tty_activity

    if control_power:
        if idle > control_power_timeout and powerstate == True: 
            print "===> power was on, turning off due to idle."
            power_off()

    # Only wait up to timeout limit to send output if we're in the middle of a line
    if (chars_since_last_crlf > 0):
        if (time.time() - starttime) > midline_timeout_secs:
            print "Midline timeout!"
            starttime=time.time()
            chars_since_last_crlf = 0
            # output = "\r\n"
            line = ''
            ser.flushInput()

    # TCP socket data. If data is received and put into the "output" buffer, 
    # the next section will block until it's done slowly sending to the loop,
    # and thus select() won't be called again until then. When select() is 
    # finally called again, the connection close from the client will be acked
    # and the client can finish. The end result of this is that the client can
    # wait for the connection close to complete and know that when it does,
    # the teletype has actually finished printing the text to paper. 
    (insock, outsock, errsock) = select.select(socklist,[],[], 0)
    for s in insock:
        if s == listen_sock:
            (connection, client_addr) = s.accept()
            print "accept from", client_addr
            socklist.append(connection)
        else:
            if chars_since_last_crlf == 0:
                try:
                    data = s.recv(4096)
                except:
                    data = ''
                if data:
                    output = output + data.replace('\n', '\r\n')
                    output = output.replace('\r\x00', '\r\n') # special case for telnet char mode
                else:
                    s.close()
                    socklist.remove(s)
            else:
                # don't do anything but accept until we're done printing
                pass

    # If we have data queued to go to the teletype.
    if output and (chars_since_last_crlf == 0):
        print "Starting to print."
        if wrap_output:
            output = linewrap(output, wrap_output)
        for c in output:
            c = c.upper()
            if c in srtl and c in sgif:
                need_shift = 'DONTCARE'
                to_send = chr(srtl[c])
            else:
                if c in srtl:
                    need_shift = 'LTRS'
                    to_send = chr(srtl[c])
                else:
                    if c in sgif:
                        need_shift = 'FIGS'
                        to_send = chr(sgif[c])
                    else:
                        print "Replacing bogus character", repr(c), "with space."
                        c = ' '
                        need_shift = 'DONTCARE'
                        to_send = chr(srtl[c])
                        # output = output.replace(c, '')
                        # continue
                        

            # if we need to send a shift first, do it
            # This would be the place to deal with unshift-on-space setups
            if (need_shift != 'DONTCARE') and (shift != need_shift):
                if need_shift == 'LTRS':
                    send_shift = LTRS
                if need_shift == 'FIGS':
                    send_shift = FIGS
                if transmit_char(send_shift) == True:
                    shift = need_shift
                else:
                    break

            # now send the character itself.
            if transmit_char(to_send) == False:
                break
            output = ''

        # leave it in LTRS. this is not great but its better than 
        # leaving in figs, i think there's a bug in the tty adapter.
        if transmit_char(LTRS) == True:
            shift = 'LTRS'

    # Data coming in from the teletype loop
    inqueue = ser.inWaiting()
    if inqueue > 0:
        # reset the tty idle time counter because a character came in
        last_tty_activity = time.time()
        if control_power:
            # do we want to actually turn power on in this case? i dunno.
            if powerstate == False:
                powerstate = True 
                print "===> assuming power has been turned on, because a char came in"

        r = ser.read(1)
        chars_since_last_crlf = chars_since_last_crlf + 1
        c = ord(r[0])
        if c == 0x1B:
            shift = "FIGS"
            continue
        if c == 0x1F:
            shift = "LTRS"
            continue
        if c == 0: # i don't think this ever happens
            print "NULL"
            continue
        if c > 31:
            asciiqueue = asciiqueue + chr(c)
            continue

        # this takes advantage of a bug in the tty-usb adapter firmware
        # where it sends "[BREAK]" in ascii even if its in passthru mode.
        # but enh, it'll work anyway since a break will corrupt the next
        # characters. 
        if '[BREAK]' in ''.join(asciiqueue):
            print "Received a BREAK!"
            asciiqueue = ''
            line = ''
            time.sleep(0.5)
            ser.flushInput()
            # also disconnect all tcp sockets on break? maybe
            if kick_sockets_on_break:
                for s in socklist:
                    if s != listen_sock:
                        s.close()
                        socklist.remove(s)

            continue

        if shift == "LTRS":
            ch = ltrs[c]
        if shift == "FIGS":
            ch = figs[c]
        now = time.time() 
        delay = now - starttime
        starttime = now
        if downshift:
            try:
                line = line + ch.lower()
            except:
                print "ERROR: ch is an int??", line, "--", repr(ch)
                pass
        else:
            line = line + ch
        # process upper/lower case switches
        if "$uc" in line:
            downshift = False
            line = line.replace('$uc', '')
        if "$LC" in line:
            downshift = True
            line = line.replace('$LC', '')
        # apply special character input macros
        for (sub,repl) in input_subs:
            line = line.replace(sub, repl)
            line = line.replace(sub.lower(), repl)
        if '\n\r' in line:
            line = line.replace('\n\r', '\r\n')
        # try to allow continuation lines ending with ///
        if line.endswith('///\r\n'):
            line = line.replace('///\r\n', '')
        # if we got a cr/nl, hand off the line
        if '\r\n' in line:
            process_line(line.rstrip())
            chars_since_last_crlf = 0
            line = ''
        if feed_sockets == 'characters':
            # character that just came in gets sent to all open tcp connections
            for s in socklist:
                if s != listen_sock:
                    try:
                        s.sendall(ch)
                    except:
                        print "Socket appeared to be dropped on send attempt, removing."
                        s.close()
                        socklist.remove(s)

        #sys.stdout.write("%.3f %d %s\r\n" % (delay, chars_since_last_crlf, ch))
        sys.stdout.write("%c" % ch)
        sys.stdout.flush()

            
print "Wtf we shouldn't get here."
