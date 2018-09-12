#!/usr/bin/env python3
import os, sys
import paramiko
import getpass
import time
import socketserver
import socket
import logging


# find ElementTree
try:
    from lxml import etree
    print("running with lxml.etree")
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
        print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
                print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    print("running with ElementTree")
                except ImportError:
                    print("Failed to import ElementTree from any known place")

DISTRIBENCH_WORKDIR = '~/formela' # no trailing slash
master_hostname = socket.gethostname()

def delay():
    """
    Delays the execution of a busy wait loop
    """
    time.sleep(300)

def timef():
    """
    Returns time as a human-readable formatted string
    """
    return str(time.strftime('%d. %m. %Y %H:%M:%S', time.localtime()))

def log(msg):
    """
    Print a formatted message to the log
    """
    logging.info(msg)

def loadMachines(f):
    """
    Load list of machines from a file
    Return: list of hostnames of machines
    """
    machines = []
    with open(f) as fMachines:
        machines = list(filter(lambda x: len(x) > 0, map(lambda l: l.rstrip('\n').rstrip('\r'), fMachines.readlines())))
    return machines

def getTasksets(config):
    """
    Load task sets from xml
    Return: list of names of task sets
    """
    xml = etree.parse(config)
    return [tag.attrib['name'] for tag in xml.findall('//tasks')]

def runSet(taskset, machine, be_config, tests_name):
    """
    Starts @taskset of @tests_name on @machine with @be_config
    """
    log("Starting %s/%s @ %s" %(tests_name, taskset, machine))
    # prepare directory for done indication
    with paramiko.client.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        try:
            client.connect(machine)
        except paramiko.ssh_exception.PasswordRequiredException as e:
            pp = getpass.getpass('Please input your passphrase: ')
            client.connect(machine, passphrase=pp)

        stdin, stdout, stderr = client.exec_command('cd ' + DISTRIBENCH_WORKDIR + ' && nohup ' + DISTRIBENCH_WORKDIR +'/run_benchmarks.cat ' + be_config + ' ' + taskset + ' ' + tests_name + ' ' + master_hostname + ' >/dev/null 2>/dev/null < /dev/null')

args = sys.argv[1:]
if len(args) < 3:
    print("Usage: %s machines benchexec_config.xml TestsName" % (sys.argv[0], ))
    sys.exit(1)

jobscount = 0
be_config  = args[1]
tests_name = args[2]
tasksets   = getTasksets(be_config)
machines   = loadMachines(args[0])

logging.basicConfig(filename='distribench_{}_{}.log'.format(tests_name, timef()),format='[%(asctime)s] %(message)s',level=logging.DEBUG)

log('Using machines: ' + ','.join(machines))
log('Detected task sets: ' + ','.join(tasksets))

log('Performing initial scheduling...')
# initially, start a taskset on each available machine
for machine in machines:
    taskset = tasksets.pop()
    runSet(taskset, machine, be_config, tests_name)
    jobscount += 1
    if len(tasksets) == 0:
        break

log('Ok, all machines should be working or tasklist is empty.')
log('Waiting for machines to finish')

server = None

class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        global jobscount
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip().decode('utf-8')
        log("{} finished: {}".format(socket.gethostbyaddr(self.client_address[0])[0], self.data))
        jobscount -= 1
        if len(tasksets) > 0:
            taskset = tasksets.pop()
            runSet(taskset, socket.gethostbyaddr(self.client_address[0])[0], be_config, tests_name)
            jobscount += 1
        log("{} jobs left".format(jobscount))
        if jobscount <= 0:
            # TODO shutdown without deadlock
            log("You can now shutdown the master node using CTRL-C")

HOST, PORT = '0.0.0.0', 9669

# Create the server, binding to localhost on port 9999
server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
# Activate the server; this will keep running until you
# interrupt the program with Ctrl-C
server.serve_forever()

log('Cool and good.')
