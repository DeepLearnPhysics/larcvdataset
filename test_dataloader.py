import os,sys
import torchvision
import ROOT
from ROOT import larcv

from larcvdataset.larcvdataset import LArCVDataSet

print "Test larcv dataset"
io = LArCVDataSet("example_dataloader.cfg")
io.dumpcfg()
print "Number of entries: ",len(io)
io.start(5)

for i in range(0,10):
    print "Batch #%d"%(i)
    data = io[i]
    print data["image"].shape, data["label"].shape

io.stop()

print "FIN"

