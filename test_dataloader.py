import os,sys
import torchvision
import ROOT
from ROOT import larcv

from larcvdataset.larcvdataset import LArCVDataSet

print "Test larcv dataset"
io = LArCVDataSet("example_dataloader.cfg")
io.dumpcfg()
print "Number of entries: ",len(io)
io.start(10)
io.stop()

