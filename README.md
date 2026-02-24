# cparrun

**cparrun** - combinated parallel run of something as multiple processes (as many as you want and each restricted by timeout).

---
Could be used as **command line utility** or **python module**.
Command line utility mode could interpret arguments as multiple combinations or run in parallel set of lines from stdin as shell commands.

Output results are in **JSON** format with separated stdout, stderr, return_code, status. \
In case of python module the result will be list of dicts and the same structure. \
Main purpose: parallel debugging/troubleshooting, mass checking or just to use with slow or unstable network/corporate utilities in parallel for more perfomance. Added timeout to avoid eternal freezing or long execution of utilities. Started like a parallel manager for mass invocation thousands of external utilities from python, evolved to a python module and then to a cli utility. Outputting results in JSON format greatly simplifies any further automatic data processing. For example you could filter from thousands some kind of "failed" and re-run them again and again (simple jq filter example is given below).

## Installation
```sh
pip install cparrun
```


## Usage
```sh
cparrun [OPTIONS] -- <command expression to expand>
```
or
```sh
<long set of commands separated by new lines> | cparrun --stdin [OPTIONS] 
```

**Options**
```
--parallel               -p  parallel processes count, default: 10
--timeout                -t  timeout for processes, default: 10 
--start_token,--start    -s  start separator for mark expandable args, default: %[  
--end_token,--end        -e  end separator for mark expandable args, default: ]% 
--stdin,--in             -i  get list of commands from stdin 
--stdin-filter-comments      filter shell comments in stdin (lines started with #), default: True 
--dry-run,--print-only       print commands without running 
--help 
```

**Examples**

A simple generator of 6 parallel ping cals to given hostnames
```
cparrun -- 'ping -c2 %[google.com, gmail.com, kubernetes.io, github.com, python.org, nonexistentdomain.example]%'
```

<details>

```
[
    {
        "task_id": "brqtmq",
        "command": "ping -c2 google.com",
        "stdout": "PING google.com (172.217.17.142): 56 data bytes\n64 bytes from 172.217.17.142: icmp_seq=0 ttl=114 time=30.617 ms\n64 bytes from 172.217.17.142: icmp_seq=1 ttl=114 time=29.582 ms\n\n--- google.com ping statistics ---\n2 packets transmitted, 2 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 29.582/30.099/30.617/0.518 ms\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    },
    {
        "task_id": "XEY5Wa",
        "command": "ping -c2 gmail.com",
        "stdout": "PING gmail.com (172.217.20.69): 56 data bytes\n64 bytes from 172.217.20.69: icmp_seq=0 ttl=114 time=30.408 ms\n64 bytes from 172.217.20.69: icmp_seq=1 ttl=114 time=29.422 ms\n\n--- gmail.com ping statistics ---\n2 packets transmitted, 2 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 29.422/29.915/30.408/0.493 ms\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    },
    {
        "task_id": "sSaF9a",
        "command": "ping -c2 kubernetes.io",
        "stdout": "PING kubernetes.io (15.197.167.90): 56 data bytes\n64 bytes from 15.197.167.90: icmp_seq=0 ttl=246 time=16.015 ms\n64 bytes from 15.197.167.90: icmp_seq=1 ttl=246 time=16.320 ms\n\n--- kubernetes.io ping statistics ---\n2 packets transmitted, 2 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 16.015/16.168/16.320/0.152 ms\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    },
    {
        "task_id": "yNICrl",
        "command": "ping -c2 github.com",
        "stdout": "PING github.com (140.82.121.4): 56 data bytes\n64 bytes from 140.82.121.4: icmp_seq=0 ttl=50 time=32.427 ms\n64 bytes from 140.82.121.4: icmp_seq=1 ttl=50 time=31.123 ms\n\n--- github.com ping statistics ---\n2 packets transmitted, 2 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 31.123/31.775/32.427/0.652 ms\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    },
    {
        "task_id": "mLZsgu",
        "command": "ping -c2 python.org",
        "stdout": "PING python.org (151.101.0.223): 56 data bytes\n64 bytes from 151.101.0.223: icmp_seq=0 ttl=55 time=22.050 ms\n64 bytes from 151.101.0.223: icmp_seq=1 ttl=55 time=22.302 ms\n\n--- python.org ping statistics ---\n2 packets transmitted, 2 packets received, 0.0% packet loss\nround-trip min/avg/max/stddev = 22.050/22.176/22.302/0.126 ms\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    },
    {
        "task_id": "7L9zon",
        "command": "ping -c2 nonexistentdomain.example",
        "stdout": "",
        "stderr": "ping: cannot resolve nonexistentdomain.example: Unknown host\n",
        "return_code": 68,
        "status": "[ERROR] FINISHED "
    }
]
```
  
</details>


The example generates a set of requests of DNS NS/SOA/MX records for given domains from DNS recursors in parallel (3x3x3=27 combinations and run them). 
Output results is JSON
```bash
cparrun --parallel=8 -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'kubernetes.io']% %['@1.1.1.1', '@8.8.8.8', @'nonexistentdomain.example.']% +short"
```

<details>
  
```

    {
        "task_id": "Bm3fRR",
        "command": "dig -t 'NS' 'google.com' '@1.1.1.1' +short",
        "stdout": "ns1.google.com.\nns4.google.com.\nns2.google.com.\nns3.google.com.\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    },
    {
        "task_id": "n8acXt",
        "command": "dig -t 'SOA' 'google.com' '@1.1.1.1' +short",
        "stdout": "ns1.google.com. dns-admin.google.com. 872309766 900 900 1800 60\n",
        "stderr": "",
        "return_code": 0,
        "status": "[OK] FINISHED"
    }, ...
    
    {
        "task_id": "cKqtGN",
        "command": "dig -t 'MX' 'facebook.com' @'nonexistingdomain.somedomain.' +short",
        "stdout": "",
        "stderr": "dig: couldn't get address for 'nonexistingdomain.somedomain.': not found\n",
        "return_code": 10,
        "status": "[ERROR] FINISHED "
    }
]
```

</details>

---


Just make combinations and print them (this example makes 3x3x3=27 combinations)
```bash
cparrun --parallel=8 --dry-run -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'facebook.com']% %['@1.1.1.1', '@8.8.8.8', @'nonexistingdomain.somedomain.']% +short"
```
---


Send of list of something to run in parallel to stdin, JSON results are filtered by jq utility (shows only ERROR here). Lines starting with '#' are ignored.
```bash
echo 'ping -c2 8.8.8.8
sleep 10
curl -s google.com
wget nonexistentdomain.com123
host example.com
host gmail.com
# this is comment and will be ignored
host example2.com
' | cparrun --stdin --timeout=2 | jq '.[] | select(.status | contains("ERROR"))'
```

<details>
  
```
{
  "task_id": "AfyBvJ",
  "command": "sleep 10",
  "stdout": null,
  "stderr": null,
  "return_code": null,
  "status": "[ERROR] TERMINATED (timeout)"
}
{
  "task_id": "hEyXJR",
  "command": "wget nonexistentdomain.com123",
  "stdout": "",
  "stderr": "Prepended http:// to 'nonexistentdomain.com123'\n--2026-02-20 21:45:16--  http://nonexistentdomain.com123/\nResolving nonexistentdomain.com123 (nonexistentdomain.com123)... failed: nodename nor servname provided, or not known.\nwget: unable to resolve host address ‘nonexistentdomain.com123’\n",
  "return_code": 4,
  "status": "[ERROR] FINISHED "
}
```

</details>

---


Simple stdin example from file. Place tons of something in file separated by new line and run them in parallel. ( # comments filtered by default)
```bash
cat 100500_commands_list.txt | cparrun --stdin --parallel=50 --timeout=5
```
---

Other examples
https://github.com/itledevs/cparrun/wiki
