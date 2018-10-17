import sys,time
import zmq
from random import randint
from zmq import ssh

from workermessages import PPP_READY, PPP_HEARTBEAT

class WorkerService(object):

    def __init__(self,identity,broker_address,
                 timeout_secs=30, heartbeat_interval_secs=2, num_missing_beats=3,
                 ssh_thru_server=None, verbosity=0):
        self._identity = u"Worker-{}".format(identity).encode("ascii")
        self._broker_address = broker_address
        self._verbosity = verbosity
        self._heartbeat_interval = heartbeat_interval_secs
        self._num_missing_beats  = num_missing_beats
        self._interval_init      = 1
        self._interval_max       = 32
        self._timeout_secs = timeout_secs
        if ssh_thru_server is not None and type(ssh_thru_server) is not str:
            raise ValueError("ssh_thru_server should be a str with server address, e.g. user@server")
        self._ssh_thru_server = ssh_thru_server

        self._context = zmq.Context(1)
        self._poller  = zmq.Poller()

        self._data_queue = []
        
        self.connect_to_broker()

    def connect_to_broker(self):
        """ create new socket. connect to server. send READY message """

        self._socket   = self._context.socket(zmq.DEALER)
        self._socket.setsockopt(zmq.IDENTITY, self._identity)
        self._poller.register(self._socket,zmq.POLLIN)
        
        if self._ssh_thru_server is None:
            if "ipc" in self._broker_address:
                # regular connection through ipc socket
                self._socket.connect("%s/%d"%(self._broker_address,1))
            else:
                # connection through tpc socket
                self._socket.connect("%s"%(self._broker_address))
            print "WorkerService[{}] socket connected to {}".format(self._identity,self._broker_address)
        else:
            raise RuntimeError("Not implemented yet")
            #ssh.tunnel_connection(self._socket, "tcp://%s:%d"%(self._broker_ipaddress,self._broker_port), self._ssh_thru_server )
            #print "WorkerService[{}] socket connected via ssh-tunnel".format(self._identity)

        self._socket.send(PPP_READY)
        print "WorkerService[{}] sent PPP_READY".format(self._identity)        

    def do_work(self):

        liveness = self._num_missing_beats
        interval = self._interval_init
        heartbeat_at = time.time() + self._heartbeat_interval
        server_heartbeat_at  = time.time() + self._heartbeat_interval
        
        while True:

            socks = dict(self._poller.poll(5)) # millisecond poll

            # Handle worker activity on backend
            if socks.get(self._socket) == zmq.POLLIN:
                #  Get message
                #  - >=3-part: envelope + content + request
                #  - 1-part HEARTBEAT -> heartbeat
                frames = self._socket.recv_multipart()
                if not frames:
                    break # Interrupted
                
                if len(frames) >=3:

                    if self._verbosity>1:
                        print "WorkerService[{}]: Replying".format(self._identity)
                    # calling child function

                    # add back client-routing envelope
                    reply = [frames[0],frames[1]]

                    if len(self._data_queue)==0:
                        if self._verbosity>1:
                            print "WorkerService[{}]: queue empty. generate data".format(self._identity)
                        self._data_queue.append( self.generate_reply() )
                    else:
                        if self._verbosity>1:                        
                            print "WorkerService[{}]: use queue. num stored={}".format(self._identity,len(self._data_queue))

                    # append reply content
                    reply.extend( self._data_queue.pop(0) )
                    # send back through the proxy
                    self._socket.send_multipart(reply)
                    
                    # received request from broker.
                    # this means its still alive: reset liveness count and time until heartbeat
                    liveness = self._num_missing_beats
                    server_heartbeat_at = time.time() + self._heartbeat_interval*(self._num_missing_beats-liveness+1)                    
                                        
                elif len(frames) == 1 and frames[0] == PPP_HEARTBEAT:
                    if self._verbosity>1:
                        print "WorkerService[{}]: Recieved Queue heartbeat".format(self._identity)
                    # reset liveness count
                    liveness = self._num_missing_beats
                    # set time until server heartbeat
                    server_heartbeat_at = time.time() + self._heartbeat_interval*(self._num_missing_beats-liveness+1)
                else:
                    print "WorkerService[{}]: Invalid message: %s".format(self._identity) % frames
                interval = self._interval_init
            else:
                # poller times out
                if time.time()>server_heartbeat_at:
                    print "WorkerService[{}]: Heartbeat failure, can't reach queue".format(self._identity)
                    liveness -= 1
                    if liveness == 0:
                        print "WorkerService[{}]: Reconnecting in %0.2fs...".format(self._identity) % interval
                        time.sleep(interval)

                        if interval < self._interval_max:
                            interval *= 2

                        # reset connection to broker
                        self._poller.unregister(self._socket)
                        self._socket.setsockopt(zmq.LINGER, 0)
                        self._socket.close()
                        self.connect_to_broker()
                        liveness = self._num_missing_beats
                    else:
                        print "WorkerService[{}]: liveness reduced to {}. keep waiting ...".format(self._identity,liveness)
                        server_heartbeat_at = time.time() + self._heartbeat_interval*(self._num_missing_beats-liveness+1)                        
                else:
                    pass

                # update queue if nothing to do
                if len(self._data_queue)<4:
                    self._data_queue.append( self.generate_reply() )
                    if self._verbosity>0:
                        print "WorkerService[{}]: fill queue to {} ...".format(self._identity,len(self._data_queue))
                else:
                    if self._verbosity>2:
                        print "WorkerService[{}]: queue full ...".format(self._identity)                    
                
            # out of poller if/then
            # is it time to send a heartbeat to the client?
            if time.time() > heartbeat_at:
                if self._verbosity>1:
                    print "WorkerService[{}]: Worker sending heartbeat".format(self._identity)
                self._socket.send(PPP_HEARTBEAT)
                heartbeat_at = time.time() + self._heartbeat_interval                
                
            # flush std out
            sys.stdout.flush()
            

        # end of while loop

        return True

    def process_message(self,frames):
        raise NotImplemented("Inherited classes must define this function")

    def generate_reply(self):
        raise NotImplemented("Inherited classes must define this function")
