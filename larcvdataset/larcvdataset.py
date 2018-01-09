import os,time
import ROOT
from larcv import larcv
larcv.PSet # touch this to force libBase to load, which has CreatePSetFromFile
from larcv.dataloader2 import larcv_threadio
import numpy as np
from torch.utils.data import Dataset

class LArCVDataset(Dataset):
    """ LArCV data set interface for PyTorch"""

    def __init__( self, cfg, fillername, verbosity=0, loadallinmem=False, randomize_inmem_data=True, max_inmem_events=-1 ):
        self.verbosity = verbosity
        self.batchsize = None
        self.randomize_inmem_data = randomize_inmem_data
        self.loadallinmem = loadallinmem
        self.max_inmem_events = max_inmem_events
        self.cfg = cfg
        
        # we setup the larcv threadfiller class, which handles io from larcv files

        # setup cfg dictionary needed for larcv_threadio
        self.filler_cfg = {}
        self.filler_cfg["filler_name"] = fillername
        self.filler_cfg["verbosity"]   = self.verbosity
        self.filler_cfg["filler_cfg"]  = self.cfg
        if not os.path.exists(self.cfg):
            raise ValueError("Could not find filler configuration file: %s"%(self.cfg))

        # we read the first line of the config file, which should have name of config parameter set
        linepset = open(self.cfg,'r').readlines()
        self.cfgname = linepset[0].split(":")[0].strip()

        # we load the pset ourselves, as we want access to values in 'ProcessName' list
        # will use these as the names of the data products loaded. store in self.datalist
        self.pset = larcv.CreatePSetFromFile(self.cfg,self.cfgname).get("larcv::PSet")(self.cfgname)
        datastr_v = self.pset.get("std::vector<std::string>")("ProcessName")
        self.datalist = []
        for i in range(0,datastr_v.size()):
            self.datalist.append(datastr_v[i])

        # finally, configure io
        self.io = larcv_threadio()        
        self.io.configure(self.filler_cfg)

        if loadallinmem:
            self._loadinmem()
            

    def __len__(self):
        if not self.loadallinmem:
            return int(self.io.fetch_n_entries())
        else:
            return int(self.alldata[self.datalist[0]].shape[0])

    def __getitem__(self, idx):
        if not self.loadallinmem:
            self.io.next()
            out = {}
            for name in self.datalist:
                out[name] = self.io.fetch_data(name).data()
        else:
            indices = np.random.randint(len(self),size=self.batchsize)
            out = {}
            for name in self.datalist:
                out[name] = np.zeros( (self.batchsize,self.alldata[name].shape[1]), self.alldata[name].dtype )
                for n,idx in enumerate(indices):
                    out[name][n,:] = self.alldata[name][idx,:]
        return out        

    def _loadinmem(self):
        """load data into memory"""
        nevents = len(self)
        if self.max_inmem_events>0 and nevents>self.max_inmem_events:
            nevents = self.max_inmem_events
        
        print "Attempting to load all ",nevents," into memory. good luck"
        start = time.time()

        # start threadio
        self.start(1)

        # get one data element to get shape        
        self.io.next()
        firstout = {}
        for name in self.datalist:
            firstout[name] = self.io.fetch_data(name).data()
            self.alldata = {}
        for name in self.datalist:
            self.alldata[name] = np.zeros( (nevents,firstout[name].shape[1]), firstout[name].dtype )
            self.alldata[name][0] = firstout[name][0,:]
        for i in range(1,nevents):
            self.io.next()
            if i%100==0:
                print "loading event %d of %d"%(i,nevents)
            for name in self.datalist:
                out = self.io.fetch_data(name).data()                    
                self.alldata[name][i,:] = out[0,:]
                
        print "elapsed time to bring data into memory: ",time.time()-start,"sec"

        # stop threads. don't need them anymore            
        self.stop()
        
    def __str__(self):
        return dumpcfg()
                
    def start(self,batchsize):
        """exposes larcv_threadio::start which is used to start the thread managers"""
        self.batchsize = batchsize
        self.io.start_manager(self.batchsize)

    def stop(self):
        """ stops the thread managers"""
        self.io.stop_manager()

    def dumpcfg(self):
        """dump the configuration file to a string"""
        print open(self.cfg).read()

