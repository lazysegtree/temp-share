

import echolib
import sys 
import socket

def create_sock_and_connect(args, client_port = 0):
    verbose = (args["verbosity"] > 1)
    sock = None
    try :
        sock = socket.socket(args['family'], socket.SOCK_STREAM)

        echolib.set_sock_options(sock, args)

        bind_address = ( args['clientaddr'], client_port)
        server_address = ( args['serveraddr'], args['port'])


        if verbose:
            print("Attempting bind")

        sock.bind(bind_address)

        if verbose:
            print("Attempting connect")

        sock.connect(server_address)

        if verbose:
            print("Socket created and connected to server")
        return sock
    except Exception as e:
        if args["verbosity"] >= 1:
            print(f"Exception in creation of socket. sock = {sock}")
        if(sock):
            sock.close()
        raise(e)
    

# give socket thats binded, connected, etc
# return 1 if successful request
def send_request(sock, args):
    server_address = ( args['serveraddr'], args['port'])

    msg = "GET / HTTP/1.1\r\n" 

    if sock.family == socket.AF_INET:
        msg += "Host: " + server_address[0] + "\r\n" 
    else:
        msg += "Host: [" + server_address[0] + "]" + "\r\n" 
    
    msg += "Connection: keep-alive\r\n" + "\r\n"

    verbose = (args["verbosity"] > 1)

    if verbose:
        print(f"Sending request \n------------\n{msg}\n----------")

    peer = sock.getpeername()
    echolib.do_sendmsg(sock, msg, peer, args['sgw'])
    msg = echolib.do_recvmsg(sock, 1024)
    if msg:
        if verbose:
            print(msg)
        return 1
    else:
        print(peer , ' : connection closed')
        return 0
