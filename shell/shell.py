#! /usr/bin/env python3

import sys, os, re


def execute_command(args):
    """Takes a list of arguments and searches through the PATH environment to try and find the directory to
        the executable and attempts to run the program."""
    # find the path to the specified command
    for directory in re.split(":", os.environ['PATH']):
        program = directory + "/" + args[0]
        try:
            os.execve(program, args, os.environ)
        except FileNotFoundError:
            pass
    # if this line is reached the command could not be found in the PATH
    os.write(2, ("%s: command not found\n" % args[0]).encode())
    sys.exit(1)


def input_redirect(args):
    """Redirects the input of a file to the input of a program"""
    # close stdin (fd 0) so it can be used to read from the file
    os.close(0)
    filename = args.pop(-1)
    try:
        # read the file with stdin (fd 0)
        os.open(filename, os.O_RDONLY)
        os.set_inheritable(0, True)
        args.pop(-1)
        execute_command(args)
    except FileNotFoundError:
        os.write(2, "File not found\n".encode())


def output_redirect(args):
    """Redirects the output of a program from fd1 to a file"""
    # close stdout (fd 1) so the command will write to the file instead
    os.close(1)
    filename = args.pop(-1)
    # open or create the file with stdout (fd 1)
    os.open(filename, os.O_CREAT | os.O_WRONLY)
    os.set_inheritable(1, True)
    args.pop(-1)
    execute_command(args)

# get exec out of the way and check if the children have the correct pipe
def main():
    while True:
        cwd = os.getcwd()
        # command = input(cwd + "$ ")
        os.write(1, ("\n%s$ " % cwd).encode())
        command = os.read(0, 100)
        command = command.decode()
        command = command.strip("\n")
        args = re.split(" ", command)
        piping = False
        firstArgs = []
        secondArgs = []
        waiting = True
        # create pipe
        pr, pw = 0, 0

        if "exit" in args:
            sys.exit(0)

        if '&' in args:
            waiting = False
            args.pop(args.index('&'))

        elif args[0] == "cd":
            if args[1][0] == "/" or args[1][0] == "\\":
                os.chdir(args[1])
                continue
            new_path = cwd + "/" + args[1]
            os.chdir(new_path)
            continue

        elif "|" in args:
            piping = True
            pr, pw = os.pipe()
            for fd in (pr, pw):
                os.set_inheritable(fd, True)
            # seperate commands
            firstArgs = args[:args.index("|")]
            secondArgs = args[args.index("|")+1:]

        # else:
        rc = os.fork()

        if rc < 0:
            os.write(2, ("Fork failed returning %d\n" % rc).encode())
            sys.exit(1)

        elif rc == 0:
            # Child process
            if piping:
                # close stdout for 1st child
                os.close(1)
                # os.close(pr)
                pw2 = os.dup(pw)
                os.set_inheritable(pw2, True)
                for fd in (pw, pr):
                    os.close(fd)
                execute_command(firstArgs)
                os.close(pw2)

            elif "<" in args:
                input_redirect(args)
            elif ">" in args:
                output_redirect(args)

            else:
                execute_command(args)

        else:
            if piping:
                rc2 = os.fork()

                if rc2 < 0:
                    os.write(2, ("Fork failed returning %d\n" % rc).encode())
                    sys.exit(1)

                elif rc2 == 0:
                    # second child process
                    # close stdin for second child
                    os.close(0)
                    pr2 = os.dup(pr)
                    os.set_inheritable(pr2, True)
                    for fd in (pr, pw):
                        # print("closing fd: %d" % fd)
                        os.close(fd)

                    execute_command(secondArgs)
                    os.close(pr2)

                if waiting:
                    os.wait()
            # only call os.wait if the user does not include an &
            # os.wait()
            if piping:
                os.close(pr)
                os.close(pw)


if __name__ == '__main__':
    main()
