#! /usr/bin/python
# The only purpose of this is to run continuously, maintaining a TCP connection
# to localhost:1099, which should be an instance of "mochad" (https://github.com/bjonica/mochad)
# which talks to a USB-connected CM19A X10 rf remote relay dongle and sends events
# to this tcp client. It accepts and parses the messages from mochad and runs shell
# commands based on them according to the "cmds" array defined at the top of this file.
# -eric volpe 3/2018

import socket, select, sys, time, re, os, subprocess
from threading import Timer
import argparse, ConfigParser

# command line arg to get config file name
parser = argparse.ArgumentParser(description='Run commands when X10 remote events are received by mochad')
parser.add_argument('-c', '--configfile', action="store", dest="configfile", required=True)
args = parser.parse_args()
# make sure we can read it.
if not os.access(args.configfile, os.R_OK):
    print "Can't read config file", args.configfile
    sys.exit(0)

# Read the config file to get the server name & port, exec timeout, and list of cmds.
# [SETTINGS]
# server_addr = 127.0.0.1
# server_port = 1099
# exec_timeout = 10
# [COMMANDS]
# HouseUnit O5 Off : /opt/ttycommands/reperf-off
# House O Bright : /bin/echo received O-Bright
# . . .
config = ConfigParser.ConfigParser()
config.optionxform = str
try:
    config.read(args.configfile)
    exec_timeout = config.getint('SETTINGS', 'exec_timeout')
    server_addr =  config.get('SETTINGS', 'server_addr')
    server_port = config.getint('SETTINGS', 'server_port')
    server = (server_addr, server_port)
    cmds = {}
    for c in config.items("COMMANDS"):
        event = tuple(c[0].split(' '))
        cmds[event] = c[1]
except Exception as e:
    print "Error reading config file", args.configfile
    print e
    sys.exit(0)
    
# Function to run a command under the shell and wait up to exec_timeout seconds for it to finish,
# and kill it and its children off if it doesn't. 

def run_command(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    kill_proc = lambda x: os.killpg(os.getpgid(x.pid), signal.SIGTERM)
    timer = Timer(exec_timeout, kill_proc, [p])
    try:
        timer.start()
        result = p.communicate()
    finally:
        timer.cancel()
    print "exec ended with status", p.returncode, "result:", result
    if result[0]:
        print "output:", result[0].replace('\n', '\r\n')
    else:
        print "no output"
    print "return code:", p.returncode
                
# Function to take a text string delivered from the mochad server, parse it, and call run_command()
# if it appears to contain something that should be acted upon. 

def process_event(data):
    res = re.search('^.*? .*? Rx RF (.*?): (\S+) Func: (\S+)', data)
    if res:
        type = res.group(1)
        unit = res.group(2)
        op = res.group(3)
        event = (type, unit, op)
        print "event=", event
        if event in cmds:
            print "command:", cmds[event]
            run_command(cmds[event])
    else:
        print "no parse", data

socklist=[]

# Function to (re)establish a TCP connection to the mochad server at 127.0.0.1:1099/tcp
def reconnect():
    global socklist
    global mochad_sock
    mochad_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mochad_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        mochad_sock.connect(server)
        socklist.append(mochad_sock)
        print "Connected to mochad on %s:%d" %server
    except:
        print "couldn't connect to mochad on %s:%d"%server

if __name__ == '__main__':
    # initial connect
    reconnect()

    # Sit around forever waiting for lines of text from the mochad server indicating
    # signals received from RF remote controls; reconnect to mochad if we get dropped.
    while 1:
        (insock, outsock, errsock) = select.select(socklist,[],[], 0.5)
        for s in insock:
            if s == mochad_sock:
                data = mochad_sock.recv(256)
                if data:
                    process_event(data)
                else:
                    print "got disconnected."
                    mochad_sock.close()
                    socklist.remove(mochad_sock)
            else:
                print "got something from some other thing"
                
        if not socklist:
            print "Trying to connect to mochad."
            time.sleep(1)
            reconnect()
        
