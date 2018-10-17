from collections import OrderedDict
import time
import sys

import zmq

from workermessages import PPP_READY,PPP_HEARTBEAT

"""
Server for ssnet. Actually, this is a broker.

Taken from Paranoid Pirate Proxy from zeroMQ Guide.
"""

class Worker(object):
    """ represents worker info/state"""
    def __init__(self, address, heartbeat_interval, heartbeat_liveness):
        self.address = address
        self.expiry = time.time() + heartbeat_interval * heartbeat_liveness

class WorkerQueue(object):
    """ queue for workers """
    def __init__(self,verbosity):
        self.queue = OrderedDict()
        self.verbosity=verbosity

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
                if self.verbosity>1:
                    print "SSNetBroker::WorkerQueue: {} expires in {}".format(address.decode("ascii"),worker.expiry-t)
        for address in expired:
            if self.verbosity>0:            
                print "SSNetBroker::WorkerQueue: Idle worker expired: %s" % address
            self.queue.pop(address, None)
            
    def next(self):
        """ get next available worker """
        address, worker = self.queue.popitem(False)
        return address

class Server:

    def __init__(self,ipaddress,heartbeat_interval_secs=1, heartbeat_liveness=5, poller_timeout_secs=1, server_verbosity=0):
        # Prepare our context and sockets
        self._ipaddress = ipaddress
        self._heartbeat_interval  = heartbeat_interval_secs
        self._heartbeat_liveness  = heartbeat_liveness
        self._poller_timeout_secs = poller_timeout_secs
        self._server_verbosity = server_verbosity
        
        self._context   = zmq.Context()
        self._frontend  = self._context.socket(zmq.ROUTER)
        self._backend   = self._context.socket(zmq.ROUTER)
        self._str_frontendip = "%s/0"%(ipaddress)
        self._str_backendip  = "%s/1"%(ipaddress)    
        self._frontend.bind(self._str_frontendip)
        self._backend.bind(self._str_backendip)
        self._workers = WorkerQueue(self._server_verbosity) # queue for workers who are either registering for work or are returning work
        if self._server_verbosity>=0:
            print("Server: initialized. bound frontend(%s) and backend(%s)"%(self._str_frontendip, self._str_backendip))

    def start(self,timeout_sec=-1):
        # note: need to handle interrupt
        # Switch messages between sockets
        if self._server_verbosity>1:        
            print "Server: start"

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
            if self._server_verbosity>1:
                print "Server: runtime=",time.time()-tstart,"secs"

            if len(self._workers)>0:
                poller = poll_both
            else:
                poller = poll_workers
            
            #socks = dict(poller.poll( self._poller_timeout_secs*1000 ))
            socks = dict(poller.poll( 10 ))
            if self._server_verbosity>1:            
                print "Server: finish poll."

            # Handle worker activity on backend
            if socks.get(self._backend) == zmq.POLLIN:
                # Use worker address for LRU routing
                frames = self._backend.recv_multipart(zmq.DONTWAIT)
                if not frames:
                    if self._server_verbosity>=0:
                        print "Server: error in backend frame"
                    break

                address = frames[0]
                self._workers.ready(Worker(address,self._heartbeat_interval,self._heartbeat_liveness))
                if self._server_verbosity>1:                
                    print "Server: added to queue worker {}. In queue=".format(address.decode("ascii")),len(self._workers)
                
                # Validate control message, or return reply to client
                msg = frames[1:]
                if len(msg) == 1:
                    if msg[0] not in (PPP_READY, PPP_HEARTBEAT):
                        print "Server: ERROR Invalid message from worker: %s" % msg
                    elif msg[0] == PPP_HEARTBEAT:
                        if self._server_verbosity>1:
                            print "Server: got heartbeat from {}".format(address.decode("ascii"))
                        pass
                else:
                    if self._server_verbosity>1:
                        print "Server: route worker {} result back to client {}".format( address.decode("ascii"), msg[0].decode("ascii") )
                    self._frontend.send_multipart(msg)

            # Handle frontend requests
            if socks.get(self._frontend) == zmq.POLLIN:
                frames = self._frontend.recv_multipart(zmq.DONTWAIT)
                if not frames:
                    print "Server: error in frontend frame"
                    break
                frames.insert(0, self._workers.next())
                if self._server_verbosity>1:
                    print "Server: send job for {} to {}".format(frames[1],frames[0])
                self._backend.send_multipart(frames)

            # Send heartbeats to idle workers if it's time
            if time.time() >= heartbeat_at:
                for worker in self._workers.queue:
                    if self._server_verbosity>1:
                        print "Server: send heartbeat"
                    msg = [worker, PPP_HEARTBEAT]
                    self._backend.send_multipart(msg)
                heartbeat_at = time.time() + self._heartbeat_interval
            else:
                if self._server_verbosity>1:                
                    print "time to next heartbeat: ",heartbeat_at-time.time()," secs"
                pass
                
            # purge expired workers
            self._workers.purge()
            if self._server_verbosity>1:            
                print "Server: purged. in queue=",len(self._workers)
                    

            # check for time-out condition.
            # change state to closing
            if timeout_sec>0 and time.time()-tstart>timeout_sec:
                print "Server: at end of life. stopping."
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

        print "Server: shutting down"
