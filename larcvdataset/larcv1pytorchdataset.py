import os,sys

from larcv1dataset import LArCV1Dataset
from torch.utils.data import Dataset

class LArCV1PyTorchDataset( Dataset, LArCV1Dataset ):

    def __init__(self,inputfile, products, store_eventids=False, randomize=False ):
        super(LArCV1PyTorchDataset,self).__init__(inputfile,products,store_eventids=False, randomize=False )
        pass
