import time
from client import ServerClient
import zmq
import zlib

import msgpack
import msgpack_numpy as m
m.patch()


class LArCVServerClient( ServerClient ):
    """ simply recieves output of larcvserverworker (through server) """

    def __init__(self, identity, broker_ipaddress):
        # Call Mother
        super( LArCVServerClient, self ).__init__( identity, broker_ipaddress )

    def get_batch(self):
        return True

    def make_outgoing_message(self):
        """ 
        we assume get_batch has set self.imgdata_dict to contain image data arrays.
        we also assume that the worker knows the data thats coming to it. an application requires creating both the client and worker.
        this is because I do not want to deal with generating a generic message protocal right now.
        """
        msg = ["request"]
        return msg
    
    def process_reply(self,frames):
        ## need to decode the products
        if len(frames)<=1:
            return False
        self.products = {}
        self.products["feeder"] = frames[0]
        data = frames[1:]
        numproducts = len(data)/2
        
        for i in xrange(numproducts):
            name   = data[2*i+0]
            x_comp = data[2*i+1]
            x_enc = zlib.decompress(x_comp)
            arr = msgpack.unpackb(x_enc,object_hook=m.decode)
            self.products[name] = arr

        return self.products
        

                
                    
    
