import os,sys,time
from multiprocessing import Process

from server import Server
from larcvserverworker import LArCVServerWorker
from larcvserverclient import LArCVServerClient

def __start_larcv2_server__(ipaddress,verbose):
    print "starting Server w/ ipaddress {}".format(ipaddress)
    server = Server(ipaddress,server_verbosity=verbose)
    server.start()

def __start_workers_v2__(identity,inputfiles,address,loadfunc,func_params,
                         batchsize,worker_verbosity,tickbackward,seed,readonly_products):
    worker = LArCVServerWorker(identity,inputfiles,address,loadfunc,
                               func_params=func_params,batchsize=batchsize,
                               verbosity=worker_verbosity,tickbackward=tickbackward,
                               readonly_products=readonly_products,seed=seed)
    worker.do_work()
    
class LArCVServer:

    def __init__(self,batchsize,identity,load_func,inputfiles,nworkers,
                 func_params={},
                 io_tickbackward=False,
                 readonly_products=None,
                 server_verbosity=0,
                 worker_verbosity=0):

        feeddir = "/tmp/feed{}".format(identity)
        address = "ipc://{}".format(feeddir) # client front end
        os.system("mkdir -p {}".format(feeddir))

        self.identity = identity
        
        # start the server
        self.pserver = Process(target=__start_larcv2_server__,args=(address,server_verbosity))
        self.pserver.daemon = True
        self.pserver.start()

        # input files
        if type(inputfiles) is str:
            self.inputfiles = [inputfiles]
        elif type(inputfiles) is list:
            for l in inputfiles:
                if type(l) is not str:
                    raise ValueError("Inputfiles argument must be list of file paths")
                if not os.path.exists(l):
                    raise ValueError("Input file does not exist")
        # split the list
        ninputfiles = len(inputfiles)
        self.workerfiles = []
        nfiles_per_worker  = ninputfiles/int(nworkers)
        if nfiles_per_worker==0:
            nfiles_per_worker = 1
            nfiles_first_worker = 1
        else:
            # first worker takes the remainder
            nfiles_first_worker = nfiles_per_worker + len(inputfiles)%int(nworkers)
        

        # create the workers
        ifile = 0
        self.pworkers = []
        for n in xrange(nworkers):
            workerfiles = []
            if n==0:
                nfiles = nfiles_first_worker
            else:
                nfiles = nfiles_per_worker
            for iwf in xrange(nfiles):
                workerfiles.append( inputfiles[ifile] )
                ifile += 1
                if ifile>=ninputfiles:
                    ifile = 0
            process = Process(target=__start_workers_v2__,
                              args=("{}-{}".format(identity,n),
                                    workerfiles,address,load_func,func_params,
                                    batchsize,worker_verbosity,io_tickbackward,
                                    n,readonly_products))
            self.pworkers.append(process)
            self.workerfiles.append(workerfiles)
            print "Files assigned to worker[{}]: ".format(n)
            for iwf,f in enumerate(workerfiles):
                print "  [{}] {}".format(iwf,f)

        for pworker in self.pworkers:
            pworker.daemon = True
            pworker.start()

        # client
        self.client = LArCVServerClient(identity,address)

        print "LArCVServer. Workers initialized. Client synced with workers. Ready to feed data."


    def get_batch_dict(self):
        ntries = 10
        status = False
        while ntries>=0 and not status:
            #print "LArCVServer: use client to ask for result"
            status = self.client.send_receive()
            if not status:
                time.wait(1)
                ntries -= 1
            if status:
                break
            
        if not status:
            raise RuntimeError("Did not receive data")
        else:
            return self.client.get_products()
        # never get here
        return None

    def __len__(self):
        raise NotImplemented("Not implemented yet")


if __name__=="__main__":
    pass
