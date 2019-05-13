import os,sys,time
from worker import WorkerService
import numpy as np
import zlib
import zmq

from larcv import larcv

import msgpack
import msgpack_numpy as m
m.patch()

os.environ["GLOG_minloglevel"] = "1"

class LArCVServerWorker( WorkerService ):
    """ This worker uses a user function to prepare data. """

    def __init__( self,identity,inputfiles,ipaddress,load_func,
                  seed=None,batchsize=None,verbosity=0,tickbackward=False,
                  fetch_ntries=10,func_params={}):
        super( LArCVServerWorker, self ).__init__(identity,ipaddress,verbosity=verbosity)

        self.tickorder = larcv.IOManager.kTickForward
        if tickbackward:
            self.tickorder = larcv.IOManager.kTickBackward

        if type(inputfiles)==str:
            self.inputfiles = [inputfiles]
        elif type(inputfiles)==list:
            self.inputfiles = inputfiles
        else:
            raise ValueError("'inputfile' must be type 'str' or 'list of str'")
            
        self.io = larcv.IOManager(larcv.IOManager.kREAD,"",self.tickorder)
        for f in self.inputfiles:
            self.io.add_in_file(f)
        self.io.initialize()
        self.nentries = self.io.get_n_entries()
        self.batchsize = batchsize
        self.products = {}
        self.compression_level = 4
        self.print_msg_size = False
        self.num_reads    = 0
        self.load_func    = load_func
        self.func_params  = func_params
        self.seed         = seed
        self.fetch_ntries = fetch_ntries
        np.random.seed(seed=self.seed)

        if not callable(self.load_func):
            raise ValueError("'load_func' argument needs to be a function returning a dict of numpy arrays")
        print "LArCVServerWorker[{}] is loaded.".format(self._identity)
        
    def process_message(self, frames ):
        """ just a request. nothing to parse
        """
        return True

    def fetch_data(self,verbose=False):
        """ load up the next data set. we've already sent out the message. so here we try to hide latency while gpu running. """

        tstart = time.time()
        
        # get data
        indices = np.random.randint(0,high=self.nentries,size=(self.batchsize+self.fetch_ntries))
        batch = []
        keylist = None
        
        for idx in indices:
            data = None
            self.io.read_entry(idx)
            data = self.load_func( self.io, **self.func_params )

            if data is not None:
                batch.append( data )
                if keylist is None:
                    keylist = batch[-1].keys()
            if len(batch)>=self.batchsize:
                break
        
        if len(batch)==0:
            raise RuntimeError("Could not load any data")

        self.products = {}
        for k in keylist:
            nchannels = 1
            datashape = batch[0][k].shape
            #print "fetchdata[{}]: ".format(k),datashape
            if len(datashape)==3:
                nchannels = datashape[0]
            self.products[k] = np.zeros( (self.batchsize,nchannels,datashape[-2],datashape[-1]), dtype=batch[0][k].dtype )
        for ib,batchdata in enumerate(batch):
            for k in keylist:
                if self.products[k].shape[1]>1:
                    self.products[k][ib,:,:,:] = batchdata[k][:,:,:]
                else:
                    #print "shape: ",k," ",self.products[k].shape," ",batchdata[k].shape
                    self.products[k][ib,0,:,:] = batchdata[k][:,:]
            
        self.num_reads += 1
        tload = time.time()-tstart
        if self._verbosity>0:
            print "LArCVServerWorker[{}] fetched data. time={} secs. nreads={}".format(self._identity,tload,self.num_reads)
        return
    
    def generate_reply(self):
        """
        our job is to return our data set, then load another
        """
        self.fetch_data()
        
        reply = [self._identity]
        totmsgsize = 0.0
        totcompsize = 0.0
        tstart = time.time()
        for key,arr in self.products.items():
                
            # encode
            x_enc = msgpack.packb( arr, default=m.encode )
            x_comp = zlib.compress(x_enc,self.compression_level)

            # for debug: inspect compression gains (usually reduction to 1% or lower of original size)
            if self.print_msg_size:
                encframe = zmq.Frame(x_enc)
                comframe = zmq.Frame(x_comp)
                totmsgsize  += len(encframe.bytes)
                totcompsize += len(comframe.bytes)
                
            reply.append( key.encode('utf-8') )
            reply.append( x_comp )

        if self._verbosity>1:
            if self.print_msg_size:
                print "LArCVServerWorker[{}]: size of array portion={} MB (uncompressed {} MB)".format(self._identity,totcompsize/1.0e6,totmsgsize/1.0e6)
            print "LArCVServerWorker[{}]: generate msg in {} secs".format(self._identity,time.time()-tstart)
        return reply
        
            

if __name__ == "__main__":
    pass


    
