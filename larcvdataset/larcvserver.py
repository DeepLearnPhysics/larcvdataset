import os,sys,time
from multiprocessing import Process

from server import Server
from larcvserverworker import LArCVServerWorker
from larcvserverclient import LArCVServerClient

def __start_larcv2_server__(ipaddress,verbose):
    print "starting Server w/ ipaddress {}".format(ipaddress)
    server = Server(ipaddress,server_verbosity=verbose)
    server.start()

def __start_workers_v2__(identity,inputfile,address,loadfunc,batchsize,worker_verbosity):
    worker = LArCVServerWorker(identity,inputfile,address,loadfunc,batchsize=batchsize,verbosity=worker_verbosity)
    worker.do_work()
    
class LArCVServer:

    def __init__(self,batchsize,identity,load_func,inputfile,nworkers,server_verbosity=0,worker_verbosity=0):

        feeddir = "/tmp/feed{}".format(identity)
        address = "ipc://{}".format(feeddir) # client front end
        os.system("mkdir -p {}".format(feeddir))

        # start the server
        self.pserver = Process(target=__start_larcv2_server__,args=(address,server_verbosity,))
        self.pserver.daemon = True
        self.pserver.start()

        # create the workers
        self.pworkers = [ Process(target=__start_workers_v2__,
                                  args=("{}-{}".format(identity,n),inputfile,address,load_func,batchsize,worker_verbosity))
                          for n in xrange(nworkers) ]
        for pworker in self.pworkers:
            pworker.daemon = True
            pworker.start()

        # client
        self.client = LArCVServerClient(identity,address)

        print "LArCV2Server. Workers initialized. Client synced with workers. Ready to feed data."


    def get_batch_dict(self):
        self.client.send_receive()
        return self.client.products

    def __len__(self):
        raise NotImplemented("Not implemented yet")


if __name__=="__main__":
    pass
