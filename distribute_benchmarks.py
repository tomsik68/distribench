#!/usr/bin/env python3
import os, sys
import paramiko
import getpass
import time
import socketserver
import socket
import logging
from lxml import etree

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

def runSet(master_hostname, distribench_workdir, taskset, machine, be_config, tests_name, tool_archive, start_script):
    """
    Starts @taskset of @tests_name on @machine with @be_config
    """
    log("Starting %s/%s @ %s" %(tests_name, taskset, machine))
    workdir = distribench_workdir + '/' + getpass.getuser() + '/' + tests_name + '/' + str(int(time.time()))

    # prepare directory for done indication
    with paramiko.client.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        try:
            client.connect(machine)
        except paramiko.ssh_exception.PasswordRequiredException as e:
            pp = getpass.getpass('Please input your passphrase: ')
            client.connect(machine, passphrase=pp)

        stdin, stdout, stderr = client.exec_command('mkdir -p ' + workdir)
        with client.open_sftp() as sftp:
            send_file(sftp, workdir + '/start', start_script)
            send_file(sftp, workdir + '/benchexec_config.xml', be_config)
            send_file(sftp, workdir + '/tool', tool_archive)

        stdin, stdout, stderr = client.exec_command('chmod +x ' + workdir + '/start')
        stdin, stdout, stderr = client.exec_command('cd ' + workdir + ' && nohup ' + workdir +'/start ' + be_config + ' ' + taskset + ' ' + tests_name + ' ' + master_hostname + ' >/dev/null 2>/dev/null < /dev/null')

def send_file(sftp, target_file, source_path):
    """
    Upload @source_path to @target_dir through @sftp
    """
    with open(source_path, 'rb') as fSource:
        with sftp.file(target_file, 'wb') as fTarget:
            while True:
                copy_buffer = fSource.read(4096)
                if not copy_buffer:
                    break
                fTarget.write(copy_buffer)


args = sys.argv[1:]
if len(args) != 6:
    print("Usage: %s machines benchexec_config.xml TestsName WorkDir ToolArchive StartScript" % (sys.argv[0], ))
    sys.exit(1)


machines = loadMachines(args[0])
be_config  = args[1]
tests_name = args[2]
distribench_workdir = args[3].rstrip('/')
tool_archive = args[4]
start_script = args[5]

jobscount = 0
master_hostname = socket.gethostname()
tasksets = getTasksets(be_config)

logging.basicConfig(filename='distribench_{}_{}.log'.format(tests_name, timef()),format='[%(asctime)s] %(message)s',level=logging.INFO)

log('Starting tests: {}'.format(tests_name))
log('Benchexec configuration: {}'.format(be_config))
log('Using machines: ' + ','.join(machines))
log('Detected task sets: ' + ','.join(tasksets))

log('Performing initial scheduling...')

# initially, start a taskset on each available machine
for machine in machines:
    taskset = tasksets.pop()
    runSet(master_hostname, distribench_workdir, taskset, machine, be_config, tests_name, tool_archive, start_script)
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
        from_host = socket.gethostbyaddr(self.client_address[0])[0]
        cmds = self.data.split(':')

        if cmds[0] == 'done':
            tn = cmds[1]
            cat = cmds[2]
            output_dir = cmds[3]
            jobscount -= 1
            if len(tasksets) > 0:
                taskset = tasksets.pop()
                runSet(master_hostname, distribench_workdir, taskset, from_host, be_config, tests_name, tool_archive, start_script)
                jobscount += 1
            log("{} jobs are running".format(jobscount))
            if jobscount <= 0:
                # TODO shutdown without deadlock
                log("You can now shutdown the master node using CTRL-C")

        elif cmds[0] == 'locked':
            tn = cmds[1]
            cat = cmds[2]
            lockmsg = cmds[3]
            log("Failed to start job {}/{}: {} is locked: {}".format(tn,cat,from_host,lockmsg))
            log('Pushing {} back into queue'.format(tn))
            tasksets.append(cat)

        else:
            log("Task at {} failed: {}".format(from_host,self.data))



HOST, PORT = '0.0.0.0', 9669

# Create the server, binding to localhost on port 9999
server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
# Activate the server; this will keep running until you
# interrupt the program with Ctrl-C
server.serve_forever()

log('Cool and good.')
