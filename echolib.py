#!/usr/bin/python3
#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2
# as published by the Free Software Foundation.
#

import argparse
import socket
import struct
import sys
import signal
import argparse
from copy import deepcopy
import config

# Setting SOL_IP option IP_FREEBIND allows us to set arbibrary UDP source
# address.
IP_FREEBIND = 15

IP_PKTINFO = 8


def handle_arguments(name, description, usage, isclient):
    argparser = argparse.ArgumentParser(prog=name, description=description)

    argparser.add_argument("-p", dest="port", action="store", help="port")
    argparser.add_argument(
        "-q", dest="quiet_mode", action="store_true", help="Silent operation"
    )

    argparser.add_argument(
        "-v", dest="verbosity", type=int, default=0, help="Verbosity level [0,1,2,3]"
    )

    argparser.add_argument("-6", dest="v6", action="store_true", help="use IPv6")
    argparser.add_argument("-S", dest="sgw", action="store", help="SGW IP address")
    argparser.add_argument("--ip-opts-buffer", dest="ip_opts_buffer", action="store", help="Custom IP Opts Buffer for IPv6 options ( Enter in Hex - Space seperated two char hex strings ")
    argparser.add_argument("--no-ip-opts", dest="no_ip_opts", action="store_true", help="Dont set IP opts")
    argparser.add_argument(
            "--version", dest="version", action="store_true", 
            help="Display version info", default=False
    )
    if isclient:
        argparser.add_argument(
            "-C", dest="connect", action="store_true", help="do connect"
        )
        argparser.add_argument(
            "-c", dest="client", action="store", help="client IP address"
        )
        argparser.add_argument(
            "-P", dest="clientport", action="store", help="client port to bind to"
        )
        argparser.add_argument(
            "-s", dest="server", action="store", help="server IP address"
        )
        argparser.add_argument(
            "-i", dest="ifname", action="store", help="local ifindex to send on"
        )
        argparser.add_argument(
            "--non-http", dest="non_http_req", action="store_true", help="should send plain custom TCP string, (non HTTP format)", default=False
        )
        argparser.add_argument(
            "--multi-interactive-req", dest="multi_interactive_req", action="store_true", help="should send more then one request (Interactive)", default=False
        )
        argparser.add_argument(
            "-t", "--threads", dest="threads", type=int, 
            help="How many threads to use for sending request. Max number of threads : " + str(config.MAX_THREADS), 
            default=1
        )
        argparser.add_argument(
            "-r", "--req-per-thread", dest="req_per_thread", type=int, help="How many requests in each thread", default=1
        )
        argparser.add_argument(
            "--req-duration", dest="req_duration", type=int, help="Keep sending request till specified time (in msec) is passed, or req_per_thread limit is reached", default=0
        )
        argparser.add_argument(
            "-d", "--delay", dest="delay", type=int, help="Delay betweek each request in msec", default=0
        )
        argparser.add_argument(
            "--starting-port", dest="starting_port", type=int, 
            help="Specify starting port number for client sockets. Default is " + str(config.DEF_STARTING_PORT),
            default = config.DEF_STARTING_PORT
        )
        argparser.add_argument(
            "--log-freq", dest="log_freq", type=int, 
            help="Specify log freq Default is " + str(config.DEF_LOG_FREQ),
            default= config.DEF_LOG_FREQ
        )
        argparser.add_argument(
            "--random-ports", dest="random_ports", action="store_true", 
            help="Use random ports for client sockets", default=False
        )

        argparser.add_argument(
            "-k", "--keepalive", dest="keepalive", action="store_true",
            help="Use keepalive connections", default=False
        )

        argparser.add_argument(
            "--no-freebind", dest="no_freebind", action="store_true",
            help="", default=False
        )
        argparser.add_argument(
            "--no-reuseaddr", dest="no_reuseaddr", action="store_true",
            help="", default=False
        )
        argparser.add_argument(
            "--no-reuseport", dest="no_reuseport", action="store_true",
            help="", default=False
        )

    else:
        argparser.add_argument(
            "-g", dest="getsockopt", action="store_true", help="get,setsockopt"
        )
    args = {}
    params = argparser.parse_args(sys.argv[1:])



    args["connect"] = False
    args["family"] = socket.AF_INET
    args["bindaddr"] = "0.0.0.0"
    args["clientaddr"] = args["bindaddr"]
    args["localifindex"] = 0
    args["port"] = 7777
    args["quiet_mode"] = False
    args["getsockopt"] = False

    args['multi_interactive_req'] = params.multi_interactive_req
    args['non_http_req'] = params.non_http_req
    args['ip_opts_buffer'] = params.ip_opts_buffer
    args['no_ip_opts'] = params.no_ip_opts
    args["threads"] = params.threads
    args['random_ports'] = params.random_ports
    args['log_freq'] = params.log_freq
    args['version'] = params.version
    args['keepalive'] = params.keepalive

    args['no_freebind'] = params.no_freebind
    args['no_reuseaddr'] = params.no_reuseaddr
    args['no_reuseport'] = params.no_reuseport

    if params.threads > config.MAX_THREADS:
        raise Exception(f"Number of thread exceeds limit. Limit {config.MAX_THREADS}, threads {params.threads}")
    args["req_per_thread"] = params.req_per_thread
    
    args["req_duration"] = params.req_duration
    args["delay"] = params.delay
    args["verbosity"] = params.verbosity
    args["starting_port"] = params.starting_port
    if params.port:
        args["port"] = int(params.port)

    if params.quiet_mode:
        args["quiet_mode"] = True

    if params.v6:
        args["family"] = socket.AF_INET6
        args["bindaddr"] = "::"

    if params.sgw:
        args["sgw"] = params.sgw
        sgw = args["sgw"]
    else:
        args["sgw"] = None
    if isclient:
        if params.connect:
            args["connect"] = True
        if params.server:
            args["serveraddr"] = params.server
        else:
            print(usage)
            exit(1)
        
        if params.client:
            args["clientaddr"] = params.client
        else:
            args["clientaddr"] = args["bindaddr"]
        if params.ifname:
            args["localifindex"] = socket.if_nametoindex(params.ifname)
    else:
        if params.getsockopt:
            args["getsockopt"] = True

    # print(f"params : {params}, args : {args}")
    return args


# return IPROTO_TCP|IPPROTO_UDP depending on socket type
def next_proto(sock):
    if sock.type == socket.SOCK_STREAM:
        return 6
    else:
        return 17


def update_sock_options(sock, args):
    opts = sock.getsockopt(socket.IPPROTO_IPV6, socket.IPV6_DSTOPTS, 24)
    if len(opts) == 24:
        print("got expected socket option len 24, setting options...")
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_DSTOPTS, opts)
    else:
        print("getsockopt() got option len %d" % len(opts))
        sock.close()

def hex_str_to_bytes(s):
    assert len(s) % 2 == 0, "String should have even length"
    buf = [int(s[i*2:i*2+2], 16) for i in range(0, len(s)-2)]
    return bytes(buf)

def spaced_hex_str_to_bytes(s):
    buf = [int(i, 16) for i in s.split()]
    return bytes(buf)


def set_sock_options(sock, args):
    
    # FREEBIND lets us to bind to fd04::/14 addr; SO_REUSEADDR avoids TIME_WAIT
    # errors between tests
    verbose = args["verbosity"] > 1
    if args["keepalive"]:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        #sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)  # Start sending probes after 10 seconds of idleness
        #sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)  # Send probes every 3 seconds
        #sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)   # Consider the connection dead after 3 unanswered probes

    if not args["no_freebind"]:
        sock.setsockopt(socket.SOL_IP,IP_FREEBIND, 1)
    if not args["no_reuseaddr"]:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if not args["no_reuseport"]:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    # https://stackoverflow.com/questions/3229860/what-is-the-meaning-of-so-reuseaddr-setsockopt-option-linux

    if args["no_ip_opts"] :
        if verbose :
            print("Done setting basic socket optoins. Will not set IP Options")
        return

    buf = bytes([0])

    if sock.family == socket.AF_INET:
        # this is equivalent to
        # Options: (20 bytes), Record Route
        # IP Option - Record Route (19 bytes)
        #     Type: 7
        #         0... .... = Copy on fragmentation: No
        #         .00. .... = Class: Control (0)
        #         ...0 0111 = Number: Record route (7)
        #     Length: 19
        #     Pointer: 20
        #     Recorded Route: 0.0.0.0
        #     Recorded Route: 0.0.210.209
        #     Recorded Route: 140.144.0.2
        #     Recorded Route: 172.24.255.160
        # IP Option - End of Options List (EOL)
        rrstruct = None
        #if args["sgw"]:
        #    rrstruct = (
        #        struct.pack("BBB", 7, 19, 20)
        #        + socket.inet_aton("0.0.0.0")
        #        + socket.inet_aton("0.0.210.209")
        #        + socket.inet_aton("140.144.0.2")
        #        + socket.inet_aton(args["sgw"])
        #        + struct.pack("B", 0)
        #    )
        if args['ip_opts_buffer']:
            rrstruct = spaced_hex_str_to_bytes(args['ip_opts_buffer'])
        else:
            if verbose:
                print("IP Options buffer, or SGW address not specified. Sending Default Buffer")
            rrstruct = spaced_hex_str_to_bytes("07 17 18 00 00 00 00 00 00 D2 D1 8C 90 00 02 01 02 03 04 33 33 33 33 00")

        buf = deepcopy(rrstruct)
        
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, rrstruct)
    else:
        # nexthdr TCP (6), optlen (2), TLV padN (4 bytes padding)
        # TLV type EXPERIMENTAL (0x1e), len 16
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVDSTOPTS, 1)
        
        mip6 = None
        #print("here..")
        if (args['sgw']):
            #print("Got SGW args")
            mip6 = struct.pack("BBBBBBBB", 6, 2, 1, 2, 0, 0, 30, 16) + \
            socket.inet_pton(socket.AF_INET6, args["sgw"])
        elif args['ip_opts_buffer']:
            #print("Got custum IP Options buffer")
            mip6 = spaced_hex_str_to_bytes(args['ip_opts_buffer'])
        else :
            if verbose:
                print("IP Options buffer, or SGW address not specified. Sending Default Buffer")
            mip6 = spaced_hex_str_to_bytes( "06 06 03 34 01 02 03 04 " + \
                                            "A1 A2 A3 A4 A5 A6 A7 A8 B1 B2 B3 B4 B5 B6 B7 B8 " + \
                                            "C0 C1 C2 C3 C4 C5 C6 C7 C8 C9 CA CB CC CD CE CF " + \
                                            "D0 D1 D2 D3 D4 D5 D6 D7 D8 D9 DA DB DC DD DE DF")
        
        # b'\x06\x02 \x01\x02\x00\x00  \x1e\x10 &
        # \x03\xc0\x10\x00 \x00\x9b\x01\xb4 \xdc\x8d\x9b\x8e \x85\xa6\x98'
        # 2603:c010:0:          9b01:b4dc:       8d9b:8e       85:a6   98
        # 2603:c010:0:9b01:b4dc:8d9b:8e85:a698
        
        # 06 02 01 02 00 00 1e 10     26 03 c0 10 00 00 9b 01 b4 dc 8d 9b 8e 85 a6 98   (24 bytes)
        #mip6 = struct.pack('BBBBBBBB', 6, 2, 1, 2, 0, 0, 30, 24) + \
        #    struct.pack('B'*24, *tuple(range(0,24)))
        
        buf = deepcopy(mip6)            
        #print("Setting them now. mip6 type : ", type(mip6))
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_DSTOPTS, mip6)
        
    actual_hex = ' '.join(format(b, "02X") for b in buf)
    #actual_binary = ' '.join(format(b, "08b") for b in buf)
    if verbose:
        print(f"Setted this as IP Options HEX : \n{actual_hex}")


def do_recvmsg(sock, size):
    data, ancillary, flags, peer = sock.recvmsg(size, size)
    local = sock.getsockname()
    localifindex = 0
    return data.decode("ascii"), peer, local, localifindex


def do_sendmsg(sock, msg, peer, sgw):
    local = sock.getsockname()
    srcaddr = socket.inet_pton(sock.family, local[0])
    try:
        sock.sendmsg([bytes(msg, "ascii")], [], 0, peer)
    except OSError as e:
        print(
            "Could not send from %s: %s, reverting to sendto()" % (local[0], format(e))
        )
        sock.sendto(bytes(msg, "ascii"), peer)


def do_recv(sock, size):
    if sock.family == socket.AF_INET6:
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVDSTOPTS, 1)
    data, peer = sock.recvfrom(size)
    return data.decode("ascii")


def do_send(sock, msg):
    sock.send(bytes(msg, "ascii"))
