import sys,time
import zmq
from random import randint
from zmq import ssh

from workermessages import PPP_READY, PPP_HEARTBEAT

class LArCVBaseWorker(object):

    def __init__(self,identity,broker_ipaddress, port=5560, timeout_secs=30, heartbeat_interval_secs=2, num_missing_beats=3, ssh_thru_server=None):
        self._identity = u"Worker-{}".format(identity).encode("ascii")
        self._broker_ipaddress = broker_ipaddress
        self._broker_port = port
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

        self.connect_to_broker()

    def connect_to_broker(self):
        """ create new socket. connect to server. send READY message """

        self._socket   = self._context.socket(zmq.DEALER)
        self._socket.setsockopt(zmq.IDENTITY, self._identity)
        self._poller.register(self._socket,zmq.POLLIN)
        
        if self._ssh_thru_server is None:
            # regular connection            
            self._socket.connect("tcp://%s:%d"%(self._broker_ipaddress,self._broker_port))
            print "LArCVBaseWorker[{}] socket connected".format(self._identity)
        else:
            ssh.tunnel_connection(self._socket, "tcp://%s:%d"%(self._broker_ipaddress,self._broker_port), self._ssh_thru_server )
            print "LArCVBaseWorker[{}] socket connected via ssh-tunnel".format(self._identity)

        self._socket.send(PPP_READY)
        print "LArCVBaseWorker[{}] sent PPP_READY".format(self._identity)        

    def do_work(self):

        liveness = self._num_missing_beats
        interval = self._interval_init
        heartbeat_at = time.time() + self._heartbeat_interval
        
        while True:

            socks = dict(self._poller.poll(self._timeout_secs * 1000))

            # Handle worker activity on backend
            if socks.get(self._socket) == zmq.POLLIN:
                #  Get message
                #  - >=3-part: envelope + content + request
                #  - 1-part HEARTBEAT -> heartbeat
                frames = self._socket.recv_multipart()
                if not frames:
                    break # Interrupted
                
                if len(frames) >=3 :

                    print "LArCVBaseWorker[{}]: Replying".format(self._identity)
                    # calling child function
                    processed = self.process_message( frames[2:] )

                    # add back client-routing envelope
                    reply = [frames[0],frames[1]]
                    # append reply content
                    reply.extend( self.generate_reply() )
                    # send back through the proxy
                    self._socket.send_multipart(reply)
                    
                    # received request from broker.
                    # this means its still alive: reset liveness count
                    liveness = self._num_missing_beats
                                        
                elif len(frames) == 1 and frames[0] == PPP_HEARTBEAT:
                    print "LArCVBaseWorker[{}]: Recieved Queue heartbeat".format(self._identity)
                    # reset liveness count
                    liveness = self._num_missing_beats
                else:
                    print "LArCVBaseWorker[{}]: Invalid message: %s".format(self._identity) % frames
                interval = self._interval_init
            else:
                # poller times out
                liveness -= 1
                if liveness == 0:
                    print "LArCVBaseWorker[{}]: Heartbeat failure, can't reach queue".format(self._identity)
                    print "ssNetWorker[{}]: Reconnecting in %0.2fs..." % interval
                    time.sleep(interval)

                    if interval < self._interval_max:
                        interval *= 2

                    # reset connection to broker
                    self._poller.unregister(self._socket)
                    self._socket.setsockopt(zmq.LINGER, 0)
                    self._socket.close()
                    self.connect_to_broker()
                    liveness = self._num_missing_beats

                
            # out of poller if/then
            # is it time to send a heartbeat to the client?
            if time.time() > heartbeat_at:
                print "LArCVBaseWorker[{}]: Worker sending heartbeat".format(self._identity)
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
