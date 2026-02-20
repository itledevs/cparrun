#!/usr/bin/env python3
import subprocess
import random
import time
from string import ascii_letters, digits
import typer
from typing import Annotated
from typing import List
import json
import sys

import logging
log = logging.getLogger(__name__)
log_handler_stderr = logging.StreamHandler(sys.stderr)
formatter_syslog = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s')
formatter_stderr = logging.Formatter('%(message)s')
log_handler_stderr.setFormatter(formatter_stderr)
log.addHandler(log_handler_stderr)
log.setLevel(logging.ERROR)


help_info = """cparrun - combinated parallel run of something as multiple processes (as many as you want and restricted by timeout)
Could be used as python module or command line utility.
Command line utility mode could interpret arguments as multiple combinations or run in parallel set of lines from stdin as shell commands.

Output results are in JSON format with separated stdout, stderr, return code, status.

USAGE EXAMPLES:
# this example makes 3x3x3=27 combinations and just print them
cparrun --parallel=8 --dry-run -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'facebook.com']% %['@1.1.1.1', '@8.8.8.8', @'nonexistingdomain.somedomain.']% +short"

# request DNS in parallel. this example makes 3x3x3=27 combinations and run them. Output results is JSON
cparrun --parallel=8 -- "dig -t %['NS', 'SOA', 'MX']% %['google.com', 'gmail.com', 'facebook.com']% %['@1.1.1.1', '@8.8.8.8', '@nonexistingdomain.somedomain.']% +short"

# send of list of everything to run to stdin, JSON results are filtered by jq utility
echo 'ping -c2 8.8.8.8
sleep 10
curl -s google.com
wget nonexistentdomain.com123
' | cparrun --stdin --timeout=2 | jq '.[] | select(.status | contains("ERROR"))'

# simple stdin example from file
cat commands.txt | cparrun --stdin --parallel=50 --timeout=5

"""


def get_random_str(generated_len=6):
    """Get random string of letters, digits """
    password_characters = ascii_letters + digits
    return ''.join(random.choice(password_characters) for i in range(generated_len))


def interpret_cmd(interpreted_cmd: str, start_token='%[', end_token=']%') -> list:
    """Interpret and converts raw command line to "expandable" list form.
    Example: "ping -n -c2 %['192.168.1.1', '192.168.1.2']%"  ->  ['ping -n -c2', ['192.168.1.1', '192.168.1.2']]
    :param interpreted_cmd: command to be interpreted
    :param start_token: start token for mark expandable list in cmd
    :param end_token: end token for mark expandable list in cmd
    :return:
    """
    start_token_len = len(start_token)
    end_token_len = len(end_token)
    expandable_list = list()
    # better than while True: to restrict
    for _i in range(1,10):
        start_index = interpreted_cmd.find(start_token)
        end_index = interpreted_cmd.find(end_token)
        if start_index == -1:
            if interpreted_cmd.strip() == '':
                break
            expandable_list.append(interpreted_cmd)
            break
        if not (start_index < end_index):
            log.error(f'[ERROR] wrong start index of start token: {start_index=} >= {end_index=};')
            break
        expandable_list.append(interpreted_cmd[:start_index])

        _list = [s.strip() for s in (interpreted_cmd[start_index + start_token_len:end_index]).split(',')]
        expandable_list.append(_list)
        interpreted_cmd = interpreted_cmd[end_index + end_token_len:]

    return expandable_list


def combinate_lists(input_list: list) -> list[list]:
    """Converts "expandable" list by unfolding nested lists to combinations
    :param input_list: something like ['ping', '-n', '-c2', ['192.168.1.1', '192.168.1.2']]
    :return: will be combinated to [['ping', '-n', '-c2', '192.168.1.1'], ['ping', '-n', '-c2', '192.168.1.2']]
    """
    expanded_list = [[]]
    for argument in input_list:

        if type(argument) not in (str, list, tuple, set):
            # exit if bad type
            log.error(f'bad type of argument: {type(argument)=};  {argument=}')
            break

        if type(argument) == str:
            for item in expanded_list:
                item.append(argument)
            continue

        if type(argument) in (list, tuple, set):
            new_expanded_list = list()
            for parameter in argument:
                for item_list in expanded_list:
                    copy_item_list = item_list[:]
                    copy_item_list.append(parameter)
                    #print(copy_item_list)
                    new_expanded_list.append(copy_item_list)
            expanded_list = new_expanded_list
    return expanded_list


def parallel_run(commands: list, shell=None, parallel=10, timeout=10, env=None) -> list[dict]:
    """ parallel run previously prepared command lists
    param: commands: command list for paralleling.
    Example: [['ping', '-n', '-c2', '192.168.1.1'], ['ping', '-n', '-c2', '192.168.1.3']] - more precise for subprocess
    or: ['ping -n -c2 192.168.1.1', 'ping -n -c2 192.168.1.3'] - string form need to be mediated by shell
    :param shell: Use shell as mediate layer (True) or not (False)
    shell = None: auto-define. if input cmd_args is list/tuple - shell=False, in case cmd_args is string - shell=True
    :param parallel:
    :param timeout: set time limit for subprocesses (seconds)
    :param env: set environment variables for passthrough
    :return: result in list of dictionaries by form: [{'task_id': str, 'command': str|list, 'stdout': str, 'stderr': str, 'return_code': int, 'status': str}, ...]
    """
    commands_len = len(commands)
    _shell = shell
    tasks = {}
    result = [None] * commands_len

    for i, cmd_args in enumerate(commands, start=0):
        task_num = i + 1
        #if (i % 100 == 0): # sometimes only every 100th
        log.debug(f'[parallel_run] launched task: {task_num} / {commands_len}')

        # auto-define in None case
        if shell is None:
            if isinstance(cmd_args, list) or isinstance(cmd_args, tuple):
                _shell = False
            elif isinstance(cmd_args, str):
                _shell = True

        log.debug(f'[parallel_run] task: {task_num}; {_shell=}')
        tasks[i] = subprocess.Popen(cmd_args, shell=_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', env=env)
        result[i] = {'task_id': get_random_str(), 'command': cmd_args[:], 'stdout': None, 'stderr': None, 'return_code': None, 'status': 'RUNNING'}
        # if desired amount of tasks started - waiting them to finish
        if (task_num % parallel) == 0 or task_num == commands_len:
            group_tasks_start_time = time.time()
            is_timeout = False
            while tasks:
                if time.time() - group_tasks_start_time >= timeout:
                    is_timeout = True
                    #log.debug(f'WARNING: {timeout=} reached')

                for key, proc in tasks.items():
                    if proc.poll() is not None:  # subprocess finished
                        p_stdout, p_stderr = proc.communicate()
                        p_return_code = proc.returncode
                        result[key]['stdout'] = p_stdout
                        result[key]['stderr'] = p_stderr
                        result[key]['return_code'] = p_return_code
                        result[key]['status'] = '[OK] FINISHED' if p_return_code == 0 else '[ERROR] FINISHED '
                        del tasks[key]  # remove from the tasks as finished
                        #log.debug(f'task finished: #{key+1}; {result[key]}')
                        break    # preventing RuntimeError: dictionary changed size during iteration
                    elif is_timeout:
                        proc.kill()
                        result[key]['stdout'] = None
                        result[key]['stderr'] = None
                        result[key]['return_code'] = None
                        result[key]['status'] = f'[ERROR] TERMINATED (timeout)'
                        del tasks[key]  # remove from the tasks as terminated
                        #log.debug(f'WARNING: task terminated (timeout): #{key+1}; {result[key]=}')
                        break
                time.sleep(0.05)
        else:
            # else do nothing here - go for another round and add more subprocesses to group
            pass
    return result


def main_cli(
    parallel: Annotated[int, typer.Option("--parallel", "-p", help="parallel processes count")] = 10,
    timeout: Annotated[int, typer.Option("--timeout", "-t", help="timeout for processes")] = 10,
    start_token: Annotated[str, typer.Option("--start_token", "--start", "-s", help="start separator for mark expandable args")] = '%[',
    end_token: Annotated[str, typer.Option("--end_token", "--end", "-e", help="end separator for mark expandable args")] = ']%',
    stdin: Annotated[bool, typer.Option("--stdin", "--in", "-i", help="get list of commands from stdin")] = False,
    stdin_filter_comments: Annotated[bool, typer.Option("--stdin-filter-comments",  help="filter shell comments in stdin (lines started with #)")] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run", "--print-only", help="print only commands without running")] = False,
    # captures everything after the " -- "
    args: List[str] = typer.Argument(None, help="command to be interpreted and paralleled--")
):
    """cparrun - combinated parallel run"""
    #log.debug(f"{parallel=}; {start_token=}; {end_token=}; {dry_run=}; {args=}")
    cmd_list = list()
    if stdin:
        for line in sys.stdin:
            # line includes the newline character, so strip() it usually
            if _line := line.strip():
                if stdin_filter_comments and _line.startswith('#'):
                    continue
                log.debug(f'[stdin]: {_line}')
                cmd_list.append(_line)

    else:
        if not args:
            log.error("[ERROR] No full set of arguments provided.")
            raise typer.Exit(1)

        args_text = " ".join(args)

        expandable_list = interpret_cmd(args_text)
        cmd_list_raw = combinate_lists(expandable_list)
        cmd_list = [''.join(_m) for _m in cmd_list_raw]

    if dry_run:
        print('[DRY RUN] List of commands:', file=sys.stderr)
        for _cmd in cmd_list:
            print(_cmd)
        return

    cmd_results = parallel_run(commands=cmd_list, parallel=parallel, timeout=timeout)
    json_string = json.dumps(cmd_results, indent=4, sort_keys=False)
    print(json_string)


def main():
    main_cli.__doc__ = help_info
    # invoke here; we don't need typer (like decorator of main_cli) in case of module import 
    typer.run(main_cli)


if __name__ == "__main__":
    main()





