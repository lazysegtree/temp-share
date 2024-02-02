import threading
from client_util import create_sock_and_connect, send_request
import time
import traceback
import config
import os

class Timer:
    def __init__(self):
        self._start_time = 0

    def start(self) -> None:
        self._start_time = time.time()

    def get_elapsed(self) -> float:
        assert self._start_time != 0, "Need to start the timer"
        return round(time.time() - self._start_time, 1)
    
    def get_elapsed_msec(self) -> int:
        assert self._start_time != 0, "Need to start the timer"
        return int( (time.time() - self._start_time, 1)*1000 )

class RequestResult:
    def __init__(self):
        self.tot_req = 0
        self.tot_success = 0
        self.tot_fail = 0
        self.tot_conn_err = 0
        self.tot_socket_err = 0
        self.tot_socket_created = 0
        self.socket_errno_cnt = {}
        self.http_code_cnt = {}
        self.success_req_port_cnt = {}
    


class GeneratorThread(threading.Thread):
    def __init__(self, idx:int, port_no: int, args, tot_req: int, delay_msec: int, req_duration_msec: int, results: RequestResult ,reuse_conn:bool = False):

        threading.Thread.__init__(self)
        self.idx = idx
        self.port_no = port_no
        self.args = args
        self.tot_req = tot_req
        self.delay_msec = delay_msec
        self.results = results
        self.req_duration_msec = req_duration_msec
        self.debug = args["verbosity"] > 0
        self.verbose =  args["verbosity"] > 1
        self.timer = Timer()
        self.reuse_conn = reuse_conn


    
    def run(self):
        self.timer.start()
        last_time = time.time()

        if self.debug:
            print(f"Starting Thread {self.idx} with port = {self.port_no}, reuse_conn = {self.reuse_conn} " + \
                  f"tot_req = {self.tot_req}"
                  )
        
        client_sock = None
        

        while self.results[self.idx].tot_req < self.tot_req :
            req_succeeded = False
            try:
                if client_sock is None:
                    client_sock = create_sock_and_connect(self.args, self.port_no)
                    self.results[self.idx].tot_socket_created += 1
                    if self.verbose:
                        print(f"Thread {self.idx}. Created client_socket : {client_sock}")
                else:
                    if self.verbose:
                        print(f"Thread {self.idx}. Reusing existing client_sock {client_sock}")

                
                send_request(client_sock, self.args)
                client_port = client_sock.getsockname()[1]

                # save port value
                if client_port not in self.results[self.idx].success_req_port_cnt:
                    self.results[self.idx].success_req_port_cnt[client_port] = 1
                else:
                    self.results[self.idx].success_req_port_cnt[client_port] += 1

                self.results[self.idx].tot_success += 1
                req_succeeded = True
            except OSError as oe:
                if self.debug:
                    print(f"Thread {self.idx} port {self.port_no}. {traceback.format_exc()}")

                if oe.errno not in self.results[self.idx].socket_errno_cnt:
                    self.results[self.idx].socket_errno_cnt[oe.errno] = 1
                else:
                    self.results[self.idx].socket_errno_cnt[oe.errno] += 1
                
            except Exception as e:
                if self.debug:
                    print(f" Thread {self.idx} port {self.port_no} Unknown Error in sending request. {traceback.format_exc()}")
                
            finally:
                if (client_sock and ((not self.reuse_conn) or (not req_succeeded)) ):
                    if self.verbose:
                        print(f"Thread {self.idx} Closing socket on port {client_sock.getsockname()[1]}")
                    client_sock.close()
                    client_sock = None

            self.results[self.idx].tot_req += 1

            if time.time() - last_time > self.args["log_freq"] :
                last_time = time.time()
                print(f"Thread {self.idx} Done {self.results[self.idx].tot_req} requests so far. {self.results[self.idx].tot_success} Successful" + \
                      f", {self.results[self.idx].tot_socket_created} sockets created")    

            time.sleep(self.delay_msec / 1000)
        
        # final cleanup in case of socket reuse.
        if client_sock:
            if self.verbose:
                print(f"Thread {self.idx} Closing socket on port {client_sock.getsockname()[1]}")
            client_sock.close()

        if self.debug:
            print(f"Thread {self.idx} Finished {self.results[self.idx].tot_req} requests." + \
                  f" {self.results[self.idx].tot_success} Successful. Time taken : {self.timer.get_elapsed()}"
                  )
            print(f"{self.results[self.idx].tot_socket_created} total sockets created")
            for client_port in self.results[self.idx].success_req_port_cnt:
                print(f"Thread {self.idx}. Socket with Port {client_port} . {self.results[self.idx].success_req_port_cnt[client_port]} Successful requests")

        
class Generator:
    def __init__(self, args):
        self.args = args
        self.cnt_thread = args["threads"]
        self.req_per_thread = args["req_per_thread"] 
        self.delay_msec = args["delay"] 
        self.reuse_conn = args["keepalive"]
        self.req_duration_msec = args["req_duration"] 
        self.starting_port = args["starting_port"]
        self.random_ports = args["random_ports"]
        self.timer = Timer()

    def generate(self):
        self.timer.start()

        threads  = []
        results = [RequestResult() for i in range(0,self.cnt_thread)]


        force_kill = False
        
        try:
            port_no = 0
            for i in range(self.cnt_thread): # [0,1,2,3.... self.cnt_thread -1]
                if not self.random_ports:
                    port_no = self.starting_port + i 

                cur_thread = GeneratorThread(idx=i, port_no=port_no, args=self.args, 
                                             tot_req=self.req_per_thread, 
                                             delay_msec=self.delay_msec, 
                                             req_duration_msec=self.req_duration_msec, 
                                             results=results, reuse_conn=self.reuse_conn)
                
                # make it exit on exit of main thread.
                # when your program quits, any daemon threads are killed automatically.
                cur_thread.setDaemon(True)
                threads.append(cur_thread)
                cur_thread.start()

            for idx in range(self.cnt_thread):
                threads[idx].join()
        except KeyboardInterrupt:
            print("Script interrupted manually")
        except Exception as e:
            print(f"Unexpected uncaught Exception in sending request. {traceback.format_exc()}")
            
        
        
        tot_success = 0
        tot_req = 0
        socket_errno_cnt = {}
        tot_socket_created = 0

        for i in range(self.cnt_thread):
            tot_success += results[i].tot_success
            tot_req += results[i].tot_req
            tot_socket_created += results[i].tot_socket_created
            for key in results[i].socket_errno_cnt.keys():
                if key not in socket_errno_cnt :
                    socket_errno_cnt[key] = results[i].socket_errno_cnt[key]
                else:
                    socket_errno_cnt[key] += results[i].socket_errno_cnt[key]


        tot_fail = tot_req - tot_success
                
        total_time_sec = self.timer.get_elapsed()        
        print(f"Generator done with {self.cnt_thread} threads in {total_time_sec}sec. {tot_req} Req, {tot_success} Successful, {tot_fail} failed." + \
              f"\n {tot_socket_created} Total sockets created")
        
        if len(socket_errno_cnt) > 0:
            print(f"Socket failures : ")
            for key in socket_errno_cnt:
                print(f"{socket_errno_cnt[key]} failures for errno {key}")
       




