import os,sys, time
import torchvision
import ROOT
from ROOT import larcv

from larcvdataset.larcvdataset import LArCVDataset


print """
===================================================================

Test/Example script for LArCVDataset

To run this, download the test data to your computer from

http://www.stanford.edu/~kterao/public_data/v0.1.0/2d/classification/five_particles/practice_train_5k.root

and put the location of the file into 'example_dataloader.cfg' 
which is found in the same directory as this script.

===================================================================
"""

# We setup the larcvdataset using the configuration file
io = LArCVDataset("example_dataloader.cfg","ThreadProcessor",loadallinmem=True)
#io.dumpcfg()

print "Number of entries: ",len(io)
io.pset
print "Data objects: ",io.datalist

print "Press [ENTER] to start filler loop"
print "Will retrieve data (dictionary of numpy arrays) and print their shapes. Enjoy."
raw_input()

io.start(50)

tottime = 0.0
nbatches = 50

start = time.time()

for i in range(0,nbatches):
    print "Batch #%d"%(i)
    data = io[i]
    for name in io.datalist:
        print " ",name,":",data[name].shape,
    print

elapsed = time.time()-start
print "Elapsed time: ",elapsed
print "time per batch: ",elapsed/nbatches

io.stop()

print "FIN"

