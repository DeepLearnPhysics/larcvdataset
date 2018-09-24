import os,sys, time
import torch
import torchvision
import ROOT
from ROOT import larcv

from larcvdataset.larcvdataset import LArCVDataset


print """
============================================================================

Test/Example script for LArCVDataset using the infrastructure for pytorch

NOT WORKING

To run this, download the test data to your computer from

http://www.stanford.edu/~kterao/public_data/v0.1.0/2d/classification/five_particles/practice_train_5k.root

and put the location of the file into 'example_dataloader.cfg' 
which is found in the same directory as this script.

=============================================================================
"""

# We setup the larcvdataset using the configuration file
io = LArCVDataset("flowloader_dualflow_test.cfg","ThreadProcessor",batchsize=1)

dataset = torch.utils.data.DataLoader( io, batch_size=4, shuffle=True, num_workers=1 )

for ibatch,batch in dataset: 
    for k,arr in batch.items():
        print k,arr.shape

    if ibatch>=3:
        break
    
print "[enter] to stop"
raw_input()
io.stop()
