""" Command parser definition """

from sys import stdout
from time import sleep

from clouds_aws.remote_stack import RemoteStack


def add_parser(subparsers):
    """
    Add command subparser
    :param subparsers:
    :return:
    """
    parser = subparsers.add_parser('events', help='output all events of a stack')
    parser.add_argument('-f', '--follow', action='store_true',
                        help='follow events until stack transition complete')
    parser.add_argument('stack', help='stack name')
    parser.set_defaults(func=cmd_events)


def cmd_events(args):
    """
    Print stack events
    :param args:
    :return:
    """
    stack = RemoteStack(args.stack)
    stack.load()
    print_events(stack.events)

    # poll forever
    if args.follow:
        try:
            while True:
                exit_if_transition_finished(stack.events)
                sleep(5)
                new_events = stack.poll_events()
                if new_events:
                    print_events(new_events)
        except KeyboardInterrupt:
            exit(0)


def exit_if_transition_finished(events):
    """
    Exits if the stack reached a stable state
    :param events:
    :return:
    """
    if events and events[-1]["ResourceType"] == "AWS::CloudFormation::Stack":
        if events[-1]["ResourceStatus"][-8:] == 'COMPLETE':
            exit(0)
        if events[-1]["ResourceStatus"] == 'DELETE_FAILED':
            exit(1)


def print_events(events):
    """
    Pretty print events
    :param events: list
    :return:
    """
    for event in events:
        event_line = "%s %s\t%s\t%s\t%s" % (
            event['Timestamp'].strftime('%Y-%m-%d/%H:%M:%S'),
            event['ResourceStatus'].ljust(18),
            event['ResourceType'].ljust(25),
            event['LogicalResourceId'],
            event.get("ResourceStatusReason", "")
        )

        # if stdout is a tty use some pretty color
        if stdout.isatty():
            attr = []
            if event['ResourceStatus'][-8:] == 'COMPLETE':
                attr.append('32')
            elif event['ResourceStatus'][-6:] == 'FAILED':
                attr.append('31')
            event_line = '\x1b[%sm%s\x1b[0m' % (';'.join(attr), event_line)

        print(event_line)
