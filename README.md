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

+ bash
+ netcat
+ sendmail (or some package with `mail` command)
+ benchexec
+ symbiotic (or other tested tool if desired)

## Setup
### First time setup

**Please note this guide is very shallow at the moment, I will eventually come up with something better and more complete.**

Each node in the cluster needs: `run_benchmarks.cat`, `cleanup`, benchexec configuration XML(`benchexec_config.xml`) in `$DISTRIBENCH_HOME` (you can pick any folder you wish).

1. Manually review `run_benchmarks.cat` and `cleanup` scripts to change configuration
2. On each node, create a `$DISTRIBENCH_HOME` folder
3. Copy `run_benchmarks.cat` and `cleanup` into `$DISTRIBENCH_HOME` of each node
4. Generate an ssh key via `ssh-keygen` on the master node
5. Install the ssh key on each machine (meaning `ssh-copy-id`); in MUNI network, it is sufficient to install the key on `aisa`

### Every time setup

1. Prepare a file called `machines` on the master node. Each line of this file contains hostname of a usable machine in the cluster
2. Prepare benchexec configuration XML and copy it onto each machine into `$DISTRIBENCH_HOME`
3. Copy benchexec configuration XML onto master node.
4. Start `./distribute_benchmarks.py` on master node (running the script without parameters reveals usage)

## What happens automagically

- each worker node clones `sv-benchmarks` repository into `/var/data/statica/`
- each worker node is locked by existence of file `/var/data/statica/distribench.lock`
- benchexec is installed into `/var/data/statica/benchexec`

## Output

Outputs of tool for every job plus benchexec configuration XML are written to: `/var/data/statica/symbiotic-$USER/$TestsName/$(date +%s)/`.
The precise name of the directory is visible in the email and also in master node log.
