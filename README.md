# cparrun

**cparrun** - combinated parallel run of something as multiple processes (as many as you want and restricted by timeout).

---
Could be used as **command line utility** or **python module**.
Command line utility mode could interpret arguments as multiple combinations or run in parallel set of lines from stdin as shell commands.

Output results are in **JSON** format (for ease of any automation) with separated stdout, stderr, return_code, status for be. JSON could be properly filtered by jq (example below).
In case of python module the result will be list of dicts - the same structure.

## Installation:
```sh
pip install cparrun
```


## Usage:

Request DNS NS, SOA, MX records for given domains from DNS recursosrs in parallel. This example makes 3x3x3=27 combinations and run them. Output results is JSON
```bash
cparrun --parallel=8 -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'facebook.com']% %['@1.1.1.1', '@8.8.8.8', @'nonexistingdomain.somedomain.']% +short"
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


Simple stdin example from file. Place tons of something in file and run it in parallel. 
```bash
cat commands.txt | cparrun --stdin --parallel=50 --timeout=5
```
---

Other examples
https://github.com/itledevs/cparrun/wiki
