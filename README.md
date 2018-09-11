# distribench - distributed benchexec starter

Allows running benchexec on multiple computers.

## Requirements

### Master Node

+ python3
+ `pip3 install -r requirements.txt`

### Worker Nodes

+ bash
+ netcat
+ sendmail (or some package with `mail` command)
+ benchexec
+ symbiotic (or other tested tool if desired)
+ sv-benchmarks

## How to run distribench

**Please note this guide is very shallow, I will eventually come up with something better and more complete.**

Each node in the cluster needs: `run_benchmarks.cat`, `cleanup`, benchexec configuration XML(`benchexec_config.xml`) in `$DISTRIBENCH_HOME` (you can pick any folder you wish).

1. On each node, create a `$DISTRIBENCH_HOME` folder.
2. Pick a master node.
3. Prepare a file called `machines` on the master node. Each line of this file contains hostname of a usable machine in the cluster.
4. Manually review `run_benchmarks.cat` and `cleanup` scripts to change configuration
5. Start `./distribute_benchmarks.py` on master node
