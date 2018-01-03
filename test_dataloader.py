import os,sys
import torchvision
import ROOT
from ROOT import larcv

from larcvdataset.larcvdataset import LArCVDataset


print """
===================================================================

Test/Example script for LArCVDataset

To run this, download the test data to your computer from

http://www.stanford.edu/~kterao/public_data/v0.1.0/2d/classification/five_particles/practice_train_5k.root

and put the location of the file into example_dataloader.cfg

===================================================================
"""

io = LArCVDataset("example_dataloader.cfg","ThreadProcessor",loadallinmem=True)
#io.dumpcfg()

print "Number of entries: ",len(io)
io.pset
print "Data objects: ",io.datalist

print "Press [ENTER] to start filler loop"
print "Will retrieve data (dictionary of numpy arrays) and print their shapes. Enjoy."
raw_input()

io.start(5)

for i in range(0,10):
    print "Batch #%d"%(i)
    data = io[i]
    for name in io.datalist:
        print " ",name,":",data[name].shape,
    print

io.stop()

print "FIN"

