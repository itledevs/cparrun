# cparrun

cparrun - combinated parallel run of something as multiple processes (as many as you want and restricted by timeout)
Could be used as python module or command line utility.
Command line utility mode could interpret arguments as multiple combinations or run in parallel set of lines from stdin as shell commands.

Output results are in JSON format with separated stdout, stderr, return code, status.

# USAGE EXAMPLES:
## this example makes 3x3x3=27 combinations and just print them
cparrun --parallel=8 --dry-run -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'facebook.com']% %['@1.1.1.1', '@8.8.8.8', @'nonexistingdomain.somedomain.']% +short"

## request DNS in parallel. this example makes 3x3x3=27 combinations and run them. Output results is JSON
cparrun --parallel=8 -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'facebook.com']% %['@1.1.1.1', '@8.8.8.8', @'nonexistingdomain.somedomain.']% +short"

## send of list of everything to run to stdin, JSON results are filtered by jq utility
echo 'ping -c2 8.8.8.8
sleep 10
curl -s google.com
wget nonexistentdomain.com123
host example.com
host example2.com
' | cparrun --stdin --timeout=2 | jq '.[] | select(.status | contains("ERROR"))'

## simple stdin example from file
cat commands.txt | cparrun --stdin --parallel=50 --timeout=5

## other examples
https://github.com/itledevs/cparrun/wiki