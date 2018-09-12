# distribench - distributed benchexec starter

Allows running benchexec on multiple computers.

## Features

+ control a cluster of computers running benchexec
+ define a cluster of machines
+ start a new job when machine finishes
+ send e-mail when a machine finishes

## Requirements

### Master Node

+ python3
+ `pip3 install -r requirements.txt` (if you don't have root access, you can still `pip3 install --user -r requirements.txt`)

### Worker Nodes

+ `ssh`
+ ability to run the startup script
+ ability to run the tool
+ linux system

## Setup
### First time setup

**Please note this guide is very shallow at the moment, I will eventually come up with something better and more complete.**

distribench requires SSH connection to every machine that is supposed to be part of the cluster. In order to reduce user interaction, it is recommended to setup SSH login via a key:

1. Generate an ssh key via `ssh-keygen` on the master node
2. Install the ssh key on each machine (meaning `ssh-copy-id`); in MUNI network, it is sufficient to install the key on `aisa`

### Every time setup

1. Prepare a file called `machines` on the master node. Each line of this file contains hostname of a usable machine in the cluster
2. Prepare benchexec configuration XML (`benchexec_config.xml`) on master node
3. Prepare client-side script on master node. It has to be exactly the same for all workers. For example client script, see [run_benchmarks.cat](https://github.com/tomsik68/distribench/blob/master/run_benchmarks.cat)
4. Prepare distribution archive of your tool on master node
5. Start `./distribute_benchmarks.py` on master node (running the script without parameters reveals usage)

## What happens automagically

- each worker node gets startup script
- each worker node gets benchexec config (in the same directory as the script)
- each worker node gets tool distribution archive (in the same directory as the script)

## What client scripts take care of

- each worker node is locked by existence of a file (client scripts in a network need to agree on the precise filename)
- install benchmarks set
- install benchexec
- extract tool archive to some folder and add it into `$PATH`
- send status reports to server
- run benchexec
- collecting tool output
