import os
import ROOT
from larcv import larcv
from larcv.dataloader2 import larcv_threadio
import numpy
from torch.utils.data import Dataset

class LArCVDataSet(Dataset):
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

        #self.pset = larcv.PSet("LArCVDataSet",open(self.cfg).read())
        
        self.io = larcv_threadio()        
        self.io.configure(self.filler_cfg)

    def __len__(self):
        return int(self.io.fetch_n_entries())

    def __getitem__(self, idx):
        self.io.next()
        data = self.io.fetch_data("image")
        labels = self.io.fetch_data("label")
        out = {"image":data.data(),"labels":labels.data()}
        return out
        

    def start(self,batchsize):
        self.batchsize = batchsize
        self.io.start_manager(self.batchsize)

    def stop(self):
        self.io.stop_manager()

    def dumpcfg(self):
        print open(self.cfg).read()
