#! /usr/bin/env python3

import sys, os, re


def execute_command(args):
    for directory in re.split(":", os.environ['PATH']):
        program = directory + "/" + args[0]
        # os.write(1, (str(os.getpid()) + " attempting to execute " + program + "\n").encode())
        try:
            os.execve(program, args, os.environ)
        except FileNotFoundError:
            pass
    os.write(2, ("%s: command not found\n" % args[0]).encode())
    sys.exit(1)


def input_redirect(args):
    os.close(0)
    filename = args.pop(-1)
    try:
        os.open(filename, os.O_RDONLY)
        os.set_inheritable(0, True)
        args.pop(-1)
        execute_command(args)
    except FileNotFoundError:
        print("No such file in directory")


def output_redirect(args):
    os.close(1)
    filename = args.pop(-1)
    os.open(filename, os.O_CREAT | os.O_WRONLY)
    os.set_inheritable(1, True)
    args.pop(-1)
    execute_command(args)


def main():
    while True:
        cwd = os.getcwd()
        # command = input(cwd + "$ ")
        os.write(1, (cwd + "$ ").encode())
        command = os.read(0, 100)
        command = command.decode()
        command = command.strip("\n")
        args = re.split(" ", command)

        if "exit" in args:
            sys.exit(0)

        elif args[0] == "cd":
            new_path = cwd + "/" + args[1]
            os.chdir(new_path)

        else:
            rc = os.fork()

            if rc < 0:
                os.write(2, ("Fork failed returning %d\n" % rc).encode())
                sys.exit(1)

            elif rc == 0:
                # Child process
                if "<" in args:
                    input_redirect(args)
                elif ">" in args:
                    output_redirect(args)
                else:
                    execute_command(args)

            else:
                # Parent process: wait for the child to terminate
                os.wait()


if __name__ == '__main__':
    main()
    