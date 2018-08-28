import time
import zmq
from collections import OrderedDict

"""
LArCVBaseClient

This class loads LArCV data products through
a proxy.

Behavior with respect to the server
1) the client requires the IP address of the server upon startup and a unique identifier
2) a timeout is defined to get a reply from the server
3) if the request times out, the client reconnects to the server and tries again
4) the client tries for self._max_times
5) if cannot finish, the client stops and return bad status

"""

class LArCVBaseClient(object):

    def __init__( self, identity, broker_ipaddress, port=5559, timeout_secs=30, max_tries=3, do_compress=True ):
        #  Prepare our context and sockets
        self._identity = u"Client-{}".format(identity).encode("ascii")
        self._broker_ipaddress = broker_ipaddress
        self._port = port
        self._max_tries = max_tries
        self._timeout_secs=timeout_secs
        self._expected_shape = (24,1,512,512)
        self._compress = do_compress
        self._load_socket()
        self.nmsgs = 0

        self._ttracker = OrderedDict()
        self._ttracker["send/receive::triptime"] = 0.0
        
    def get_batch(self):
        """ public interface. get batch of data."""
        return self._send_receive()

    def process_reply( self, msg ):
        raise NotImplementedError('process_reply Must be implemented by the subclass.')
    
    def print_time_tracker(self):
        print "=============  TimeTracker =============="
        print "number of messages: ",self.nmsgs
        for k,v in self._ttracker.items():
            print k,": ",v," secs total"
        print "========================================="    

    def _load_socket(self):
        """ internal function. load socket to server. """
        self._context  = zmq.Context()
        self._socket   = self._context.socket(zmq.REQ)        
        self._socket.identity = self._identity
        self._socket.connect("tcp://%s:%d"%(self._broker_ipaddress,self._port))
        self._poller = zmq.Poller()
        self._poller.register( self._socket, zmq.POLLIN )
        print "LArCVBaseClient[{}] socket connected to server".format(self._identity)    

    def _send_receive(self):
        """ routine that interfaces with the server socket
        -- idea is to provide one batch of data
        -- send request for data
        -- parse request w/ user supplied concrete child class (process_reply)
        """
        msg = ["request"]
        
        retries_left = self._max_tries

        troundtrip = time.time()

        while retries_left>0:
        
            # send request
            for part in msg[:-1]:
                self._socket.send(part, zmq.SNDMORE)
            self._socket.send(msg[-1])

            socks = dict(self._poller.poll(self._timeout_secs*1000))
            if socks.get(self._socket) == zmq.POLLIN:
                # got message back
                reply = self._socket.recv_multipart()
                if not reply:
                    break
                
                # process reply
                print "LArCVBaseClient[{}] received reply.".format(self._identity)
                troundtrip = time.time()-troundtrip
                self._ttracker["send/receive::triptime"] += troundtrip
                self.nmsgs += 1
                return self.process_reply( reply )
                
            else:
                # timed out
                print "LArCVBaseClient[{}] no reply from server. retrying ...".format(self._identity)
                self._socket.setsockopt(zmq.LINGER, 0)
                self._socket.close()
                self._poller.unregister(self._socket)
                retries_left -= 1
                if retries_left > 0:
                    self.load_socket()
                

        # should not get here
        troundtrip = time.time()-troundtrip
        self._ttracker["send/receive::triptime"] += troundtrip

        raise RuntimeError("LArCVBaseClient[{}] Server seems to be offline, abandoning".format(self._identity))
        return None

