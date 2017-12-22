import ROOT
from larcv import larcv
from larcv.dataloader2 import larcv_threadio
import numpy

proc = larcv_threadio()

filler_cfg = {"filler_name":"ThreadProcessor",
              "verbosity":0,
              "filler_cfg":"example_dataloader.cfg"}
proc.configure(filler_cfg)

proc.start_manager(10)
