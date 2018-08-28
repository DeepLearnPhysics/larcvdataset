from collections import OrderedDict
import time
import sys

import zmq

from workermessages import PPP_READY,PPP_HEARTBEAT

"""
Proxy server/broker.

Taken from Paranoid Pirate Proxy from zeroMQ Guide.
"""

class Worker(object):
    """ represents worker info/state"""
    def __init__(self, address, heartbeat_interval, heartbeat_liveness):
        self.address = address
        self.expiry = time.time() + heartbeat_interval * heartbeat_liveness

class WorkerQueue(object):
    """ queue for workers """
    def __init__(self):
        self.queue = OrderedDict()

    def __len__(self):
        return len(self.queue)
        
    def ready(self, worker):
        """ add ready worker to queue """
        # first pop out worker if already in queue for some reason
        self.queue.pop(worker.address, None)
        self.queue[worker.address] = worker

    def purge(self):
        """Look for & kill expired workers."""
        t = time.time()
        expired = []
        for address,worker in self.queue.iteritems():
            if t > worker.expiry:  # Worker expired
                expired.append(address)
            else:
                print "SSNetBroker::WorkerQueue: {} expires in {}".format(address.decode("ascii"),worker.expiry-t)
        for address in expired:
            print "SSNetBroker::WorkerQueue: Idle worker expired: %s" % address
            self.queue.pop(address, None)
            
    def next(self):
        """ get next available worker """
        address, worker = self.queue.popitem(False)
        return address

class LArCVServer:

    def __init__(self,ipaddress,frontendport=5559,backendport=5560, heartbeat_interval_secs=1, heartbeat_liveness=5, poller_timeout_secs=1):
        # Prepare our context and sockets
        self._ipaddress = ipaddress
        self._heartbeat_interval  = heartbeat_interval_secs
        self._heartbeat_liveness  = heartbeat_liveness
        self._poller_timeout_secs = poller_timeout_secs
        
        self._context   = zmq.Context()
        self._frontend  = self._context.socket(zmq.ROUTER)
        self._backend   = self._context.socket(zmq.ROUTER)
        self._str_frontendip = "tcp://%s:%s"%(ipaddress,frontendport)
        self._str_backendip  = "tcp://%s:%s"%(ipaddress,backendport)        
        self._frontend.bind(self._str_frontendip)
        self._backend.bind(self._str_backendip)
        self._workers = WorkerQueue() # queue for workers who are either registering for work or are returning work
        print("LArCVServer: initialized. bound frontend(%s) and backend(%s)"%(self._str_frontendip, self._str_backendip))

    def start(self,timeout_sec=-1):
        # note: need to handle interrupt
        # Switch messages between sockets
        print "LArCVServer: start"

        # Initialize pollers

        # poll with backend only when queue is empty
        poll_workers = zmq.Poller()
        poll_workers.register(self._backend, zmq.POLLIN)
        
        # poll for when workers available
        poll_both    = zmq.Poller()
        poll_both.register(self._backend,  zmq.POLLIN)
        poll_both.register(self._frontend, zmq.POLLIN)        


        # time to send next heartbeat
        heartbeat_at = time.time() + self._heartbeat_interval
        
        tstart = time.time()

        
        while True:
            #print "LArCVServer: runtime=",time.time()-tstart,"secs"

            if len(self._workers)>0:
                poller = poll_both
            else:
                poller = poll_workers
            
            socks = dict(poller.poll(self._poller_timeout_secs*1000))
            print "LArCVServer: finish poll."

            # Handle worker activity on backend
            if socks.get(self._backend) == zmq.POLLIN:
                # Use worker address for LRU routing
                frames = self._backend.recv_multipart()
                if not frames:
                    print "LArCVServer: error in backend frame"
                    break

                address = frames[0]
                self._workers.ready(Worker(address,self._heartbeat_interval,self._heartbeat_liveness))
                print "LArCVServer: added to queue worker {}. In queue=".format(address.decode("ascii")),len(self._workers)
                
                # Validate control message, or return reply to client
                msg = frames[1:]
                if len(msg) == 1:
                    if msg[0] not in (PPP_READY, PPP_HEARTBEAT):
                        print "LArCVServer: ERROR Invalid message from worker: %s" % msg
                    elif msg[0] == PPP_HEARTBEAT:
                        print "LArCVServer: got heartbeat from {}".format(address.decode("ascii"))
                else:
                    print "LArCVServer: route worker {} result back to client {}".format( address.decode("ascii"), msg[0].decode("ascii") )
                    self._frontend.send_multipart(msg)

                # Send heartbeats to idle workers if it's time
                if time.time() >= heartbeat_at:
                    for worker in self._workers.queue:
                        msg = [worker, PPP_HEARTBEAT]
                        self._backend.send_multipart(msg)
                    heartbeat_at = time.time() + self._heartbeat_interval

            # Handle frontend requests
            if socks.get(self._frontend) == zmq.POLLIN:
                frames = self._frontend.recv_multipart()
                if not frames:
                    print "LArCVServer: error in frontend frame"
                    break
                frames.insert(0, self._workers.next())
                print "LArCVServer: send job for {} to {}".format(frames[1].decode("ascii"),frames[0].decode("ascii"))
                self._backend.send_multipart(frames)

            # purge expired workers
            self._workers.purge()
            print "LArCVServer: purged. in queue=",len(self._workers)
                    

            # check for time-out condition.
            # change state to closing
            if timeout_sec>0 and time.time()-tstart>timeout_sec:
                print "LArCVServer: at end of life. stopping."
                break

            sys.stdout.flush()
            
        # End of main loop
        # do we tell workers to stop? 
        #for worker in self._workers:
        #    self._backend.send_multipart([worker,b"",b"NOCLIENT",b"",b"__BROKER_STOPPING__"])
            
        return 
                    
    def stop(self):
        
        self._backend.close()
        self._frontend.close()
        self._context.term()

        print "LArCVServer: shutting down"
