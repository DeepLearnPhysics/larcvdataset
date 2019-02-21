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
        products = {}
        
        if len(frames)<=1:
            #print "no data frames?: ",frames
            return products

        # we provide the name of the worker that did the work
        products["feeder"] = frames[0]
        data = frames[1:]
        numproducts = len(data)/2


        for i in xrange(numproducts):
            name   = data[2*i+0]
            if "__b" in name:
                # this is part of a batch
                bid = int(name.split("__b")[-1].strip())
                name = name.split("__b")[0].strip()
            else:
                bid = None
            x_comp = data[2*i+1]
            x_enc = zlib.decompress(x_comp)
            arr = msgpack.unpackb(x_enc,object_hook=m.decode)
            if bid is not None:
                # part of batch
                if name not in products:
                    products[name] = {}
                products[name][bid] = arr
            else:
                products[name] = arr

        # replace dict with list
        outproducts = {}
        for key,data in products.items():
            if type(data) is dict:
                nitems = max(data.keys())+1
                ldata = []
                for i in xrange(nitems):
                    if i in data:
                        ldata.append(data[i])
                    else:
                        ldata.append(np.zeros(1, dtype=np.float))
                outproducts[key] = ldata # replace
            else:
                outproducts[key] = data
                

        return outproducts
        
    def get_products(self):
        return self.products
