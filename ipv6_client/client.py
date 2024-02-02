import echolib
import sys
from client_util import create_sock_and_connect, send_request
from req_gen import Generator
import signal
import config

args = echolib.handle_arguments(
              f'stream_echoclient {config.VERSION}\n{config.VERSION_INFO}\n',
              'echoclient used to send requests/receive responses from server',
              f'stream_echoclient {config.VERSION}\n{config.VERSION_INFO}\n {sys.argv[0]} [-p port] -s [server IP address] [-q] .',
              True)

if(args["verbosity"] >= 3):
    print(f"Args : {args}")

if(args["version"]):
    print(f'stream_echoclient {config.VERSION}\n{config.VERSION_INFO}')
    sys.exit(0)

# so that keyboardinterrupt is caught
signal.signal(signal.SIGINT, signal.default_int_handler)

Generator(args).generate()
