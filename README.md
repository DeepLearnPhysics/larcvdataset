# larcvdataset

This module defines interfaces to LArCV 1 and 2 data.

We attempt to support

* pytorch's Dataset interface
* tensorflows's tf.data Dataset operation interface 

This module assumes

* ROOT6: LArCV2's primary dependency
* numpy: an optional LArCV2 dependency but necessary for LArCV2's python interface
* LArCV1 or LArCV2 is built and the proper environment variables have been setup (via configure.sh).
  Note that you can only have one set up in a given shell at a time!

## Installing this module

### Option 1

Set the path of the module to `PYTHONPATH`.

    export PYTHONPATH=[location of this folder]:${PYTHONPATH}

or go into this folder and run `setenv.sh`

    source setenv.sh


### Option 2

(Eventually will add an installer script.)

### If you need the LArCV1DatasetOp for Tensorflow

You need to build it. From the top repository folder (same place as this readme):

    make


## Using the module (LArCV2)

To create an instance of the dataset loader:

    from larcvdataset import LArCVDataset

    io = LArCVDataset("example_dataloader.cfg")

where `example_dataloader.cfg`, which can be found in this folder, can be your configuration file for your input.

Dump the current configuration

    io.dumpcfg()

Start the threads to load data

    io.start(10)

where `10` is the batch size. You can change this as you see fit.

To get data, just use the `[i]` operator. where `i` is an integer.
Note that right now, the value of `i` is not used.
This operator returns a dictionary with data.
See the example script (described below) as an example of how to use it.

To stop the threads before cleaning up

  io.stop()

### Example script

You can use `test_dataloader.py` to test the setup.

You can use the test training data from deep learning physics. You can get it at (via `wget`):

    wget http://www.stanford.edu/~kterao/public_data/v0.1.0/2d/classification/five_particles/practice_train_5k.root

You'll need to edit `example_dataloader.cfg` and change

    ...
    InputFiles: ["[location of the training file]"]
    ...


Note that the configuration file is setup to work with `practice_train_5k.root`.
It assumes the image data is in the tree named `data` and has PID labels in the tree named `mctruth`.
If you use another LArCV2 file, you might have to change these names.

Also, the file has 5 particle types in it.  So `ProcessList::label::PdgClassList` has the corresponding values:

    ...
    PdgClassList: [2212,11,211,13,22]
    ...

Again, if you are using another LArCV2 file, you might have to change this.

## Using the Module (LArCV1)

To create an instance of the dataset loader for LArCV1:

    import ROOT
    from larcv import larcv
    from larcvdataset import LArCV1Dataset
    productlist = [(larcv.kProductImage2D,"wire"),(larcv.kProductImage2D,"segment")]
    io = LArCV1Dataset( "mydata.root", productlist, randomize=True )

That's it. The product list is a list of tuples pairing the type of larcv1 data product with the name of the tree in the file.
Currently only `larcv.kProductImage2D` and `larcv.kProductBBox2D` are supported.

If you have a larcv1 file and want to know what the names of your trees might be, you can

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

### test script

You can test the interface out with `test_larcv1_img2d.py`.  To run it,

    python test_larcv1_img2d.py mydata.root wire segment ts_keyspweight

Note that the above uses the tree names in the above example.


