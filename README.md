# larcvdataset

Module to help load LArCV data into pytorch and tensorflow

We attempt to support

* pytorch's Dataset interface [primary focus]
* tensorflows's tf.data Dataset operation interface  [to do]

# What this module is trying to do

LArCV ROOT files typically contain images which we want to load and pass to deep learning frameworks.
See the brief [section](#structure-of-larcv-root-files) on the contents of the larcv root file.

We aim to load images along with meta-data:
* as fast as possible and
* with user flexibility of how that data is returned

We do this by asking the user to define a function that simply returns a dictionary for one training or deployment example.
Here is a quick example where we are trying to load a set of images for an entry:

```
def load_data( io ):
  # load libraries
  from larcv import larcv
  import numpy as np

  # dictionary we fill
  data = {}

  # get event container: we assume that the entry in our ROOT trees have been set and loaded
  ev_adc = io.get_data("image2d","adc") # get event container of image2d's for tree (named 'adc')

  # info about the container
  nimgs  = ev_adc.Image2DArray().size()
  if nimgs==0:
    data["adc"] = None
    return data

  #ImageMeta object which contains coordinate information for image
  # that is, how we connect pixel coordinates (row,col)
  #   into detector image coordinates (tick,wire) -- obviously in the context of LArTPCs
  #   but this can be for any (x,y) coordinate imposed over (row,col)
  meta   = ev_adc.Image2DArray().front().meta() 
  height = meta().rows()
  width  = meta().cols()

  # we create an array to hold all the data.
  # we know in this case the images in our container is all the same size
  data["adc"] = np.zeros( nimgs, height, width )

  # convert into numpy array (format passable to pytorch and tensorflow)
  # transpose is usually done to make data have same (row,col) meaning as in C++
  for iimg in xrange(nimgs):
    data["adc"][iimg,:,:] = larcv.as_ndarray( ev_adc.as_vector()[0] ).transpose(1,0)

  return data
```

By providing this function to the user, we provide flexibilty.
Of course, sometimes, users like "just gimme the images in the file, yo".
We provide a class (*to be written -- sorry*) that you can use to do this common task.

We will our event loading function into a "server" (instance of `LArCVServer` class)
which will create workers, whose job is to load images
from the file into memory and pass it to the server upon request.
This is our attempt at speed.

Here is us setting this up (assume we defined a function `load_data` to do the above):

```
# a server
batchsize = 4
nworkers  = 4
print "start feeders"
inputfile = "my_larcv_file.root"
server = LArCVServer(batchsize,"test",load_data,inputfile,nworkers,server_verbosity=0,worker_verbosity=0)
```

With that setup, we can begin to grab images:

```
print "start receiving"
nentries = 50
tstart = time.time()
for n in xrange(nentries):
  batch = feeder.get_batch_dict()
  print "entry[",n,"] from ",batch["feeder"],": ",batch.keys()
tend = time.time()-tstart
print "elapsed time, ",tend,"secs ",tend/float(nentries)," sec/batch"
```

You can find this whole example in the repository file, `test_server.py`.
You can use this to see how fast you can load images.
Hopefully, we're talking 100 milliseconds or so.

# Dependencies

* [larcv](https://github.com/larbys/larcv): library defining image and meta-data formats. with LArTPC's in mind
* [ROOT6](https://github.com/root-project/root): primary larcv dependency. provides file IO with c++ serialization and compression,
  easy generation of python bindings,
  statistical analysis tools, and plotting functions
* [numpy](http://www.numpy.org/): data objects are usually converted from larcv into numpy arrays

# Installing this module

## Option 1

Set the path of the module to `PYTHONPATH`.

    export PYTHONPATH=[location of this folder]:${PYTHONPATH}

or go into this folder and run `setenv.sh`

    source setenv.sh


## Option 2

(Eventually will add an installer script.)

## If you need the LArCV1DatasetOp for Tensorflow

You need to build it. From the top repository folder (same place as this readme):

    make


# Setting up the modeul

(to do) Environment variables, loading the dependencies, etc.

# Appendix

## Structure of LArCV ROOT files

Data inside a LArCV ROOT file is organized into different `Trees`.
Each tree is made out of `Entries` with each entry holding a container with zero or more instances of a certain class.

For example, if you have a larcv1 file and want to see the contents, do:

    > root mydata.root
    > .ls
    
you'll see something like

```
root [0] 
Attaching file mydata.root as _file0...
(TFile *) 0x563126201fb0
root [1] .ls
TFile**		mydata.root	
 TFile*		mydata.root	
  KEY: TTree	image2d_wire_tree;45	wire tree
  KEY: TTree	image2d_ts_keyspweight_tree;17	ts_keyspweight tree
  KEY: TTree	image2d_segment_tree;13	segment tree
  KEY: TTree	image2d_segment_tree;12	segment tree
  KEY: TTree	partroi_segment_tree;1	segment tree
  ...
root [2] 
```

The ROOT trees which store `Image2D` are, unsurprisingly, prefixed with `image2d_`. The name of the tree is the string between `image2d_` and `_tree`.

