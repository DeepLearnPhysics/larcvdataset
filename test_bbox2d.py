import os,sys,time
import torchvision
import ROOT
from ROOT import larcv

from larcvdataset.larcvdataset import LArCVDataset


"""
===================================================================

Test script for loading larcv::BBox2D using LArCVDataset

===================================================================
"""

cfg="""BBox2DTest:{
  Verbosity: 3
  NumThreads: 2
  NumBatchStorage: 2
  RandomAccess: true
  InputFiles: ["larcv2_michel.root"]
  ProcessName: ["bboxp0","bboxp1","bboxp2"]
  ProcessType: ["BatchFillerBBox2D","BatchFillerBBox2D","BatchFillerBBox2D"]

  ProcessList: {
    bboxp0: {
      BBox2DProducer: "boundingbox"
      ProjectionID: 0
      MaxNumBoxes: 5
      ConvertXYtoPixel: true
      ImageProducerForMeta: "wire"
    }
    bboxp1: {
      BBox2DProducer: "boundingbox"
      ProjectionID: 1
      MaxNumBoxes: 5
      ConvertXYtoPixel: true
      ImageProducerForMeta: "wire"
    }
    bboxp2: {
      Verbosity: 3
      BBox2DProducer: "boundingbox"
      ProjectionID: 2
      MaxNumBoxes: 5
      ConvertXYtoPixel: true
      ImageProducerForMeta: "wire"
    }
  }
}
"""

f = open("bboxloader.cfg",'w')
print >> f,cfg
f.close()

io = LArCVDataset("bboxloader.cfg","BBox2DTest",loadallinmem=False)

batchsize = 2
nbatches = 5

io.start(batchsize)

start = time.time()
for i  in range(0,nbatches):
    data = io[0]
    for name in io.datalist:
        print " ",name,":",data[name].shape
        print data[name].reshape( (batchsize,5,1,4) )
    print

elapsed = time.time()-start
print "Elapsed time: ",elapsed
print "time per batch: ",elapsed/nbatches

io.stop()

print "FIN"
        
