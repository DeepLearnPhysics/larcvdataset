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

    def __init__( self,identity,inputfile,ipaddress,load_func,batchsize=None,verbosity=0,tickbackward=False):
        super( LArCVServerWorker, self ).__init__(identity,ipaddress,verbosity=verbosity)
        if type(inputfile) is str:
            self.inputfiles = [inputfile]
        elif type(inputfile) is list:
            self.inputfiles = inputfile
        else:
            raise ValueError("argument inputfile should be either str or list. received {}".format(type(inputfile)))
            
        if not tickbackward:
            self.io = larcv.IOManager(larcv.IOManager.kREAD,identity)
        else:
            # this supports reading old larcv1 data
            self.io = larcv.IOManager(larcv.IOManager.kREAD,identity,larcv.IOManager.kTickBackward)
        for ifile in self.inputfiles:
            self.io.add_in_file(ifile)
        self.io.initialize()
        self.nentries = self.io.get_n_entries()
        self.batchsize = batchsize
        self.compression_level = 4
        self.print_msg_size = False
        self.num_reads = 0
        self.load_func = load_func
        if not callable(self.load_func):
            raise ValueError("'load_func' argument needs to be a function returning a dict of numpy arrays")
        print "LArCVServerWorker[{}] is loaded.".format(self._identity)
        
    def process_message(self, frames ):
        """ just a request. nothing to parse
        """
        return True

    def fetch_data(self):
        """ load up the next data set. we've already sent out the message. so here we try to hide latency while gpu running. """

        tstart = time.time()
        # get data
        # we set the seed with the time before calling random
        maxtries = 100
        np.random.seed(seed=None)
        indices = np.random.randint(0,high=self.nentries,size=(self.batchsize+maxtries))
        batch = []

        itry = 0
        while (len(batch)<self.batchsize and itry<maxtries):
            idx = indices[itry]
            data = None
            self.io.read_entry(idx)
            data = self.load_func(self.io)
            if data is not None:
                batch.append( data )
            else:
                print "LArCVServerWorker[{}] fetched data return none, try {} of {}".format(self._identity,itry+1,maxtries)
                pass # try again
            itry += 1
            
        self.num_reads += 1
        tload = time.time()-tstart
        if self._verbosity>0:
            print "LArCVServerWorker[{}] fetched data. time={} secs. nreads={}".format(self._identity,tload,self.num_reads)
        return batch
    
    def generate_reply(self):
        """
        our job is to return our data set, then load another
        """
        batch_data = self.fetch_data()
        
        reply = [self._identity]
        totmsgsize = 0.0
        totcompsize = 0.0
        tstart = time.time()
        for ibatch,batch in enumerate(batch_data):
            for key,arr in batch.items():
                if len(batch_data)>0:
                    name = "{}__b{}".format(key,ibatch)
                else:
                    name = key
                # encode
                x_enc  = msgpack.packb( arr, default=m.encode )
                x_comp = zlib.compress(x_enc,self.compression_level)

                # for debug: inspect compression gains (usually reduction to 1% or lower of original size)
                if self.print_msg_size:
                    encframe = zmq.Frame(x_enc)
                    comframe = zmq.Frame(x_comp)
                    totmsgsize  += len(encframe.bytes)
                    totcompsize += len(comframe.bytes)

                # message is alternating series of name and numpy array
                reply.append( name.encode('utf-8') )
                reply.append( x_comp )

        if self._verbosity>1:
            if self.print_msg_size:
                print "LArCVServerWorker[{}]: size of array portion={} MB (uncompressed {} MB)".format(self._identity,totcompsize/1.0e6,totmsgsize/1.0e6)
            print "LArCVServerWorker[{}]: generate msg in {} secs".format(self._identity,time.time()-tstart)
        return reply
        
            

if __name__ == "__main__":
    pass


    
