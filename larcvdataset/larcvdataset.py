import os
import ROOT
from larcv import larcv
larcv.PSet # touch this to force libBase to load, which has CreatePSetFromFile
from larcv.dataloader2 import larcv_threadio
import numpy
from torch.utils.data import Dataset

class LArCVDataset(Dataset):
    """ LArCV data set interface for PyTorch"""

    def __init__( self, cfg, verbosity=0 ):
        self.verbosity = verbosity
        self.batchsize = None

        self.cfg = cfg        
        self.filler_cfg = {}
        self.filler_cfg["filler_name"] = "ThreadProcessor"
        self.filler_cfg["verbosity"]   = self.verbosity
        self.filler_cfg["filler_cfg"]  = self.cfg
        if not os.path.exists(self.cfg):
            raise ValueError("Could not find filler configuration file: %s"%(self.cfg))

        linepset = open(self.cfg,'r').readlines()
        self.cfgname = linepset[0].split(":")[0].strip()
        self.pset = larcv.CreatePSetFromFile(self.cfg,self.cfgname).get("larcv::PSet")(self.cfgname)
        datastr_v = self.pset.get("std::vector<std::string>")("ProcessName")
        self.datalist = []
        for i in range(0,datastr_v.size()):
            self.datalist.append(datastr_v[i])
        
        self.io = larcv_threadio()        
        self.io.configure(self.filler_cfg)

    def __len__(self):
        return int(self.io.fetch_n_entries())

    def __getitem__(self, idx):
        self.io.next()
        out = {}
        for name in self.datalist:
            out[name] = self.io.fetch_data(name).data()
        return out
        

    def start(self,batchsize):
        self.batchsize = batchsize
        self.io.start_manager(self.batchsize)

    def stop(self):
        self.io.stop_manager()

    def dumpcfg(self):
        print open(self.cfg).read()
