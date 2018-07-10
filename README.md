# larcvdataset

This module defines a concrete instance of the pytorch Dataset class. It serves as an interface to data stored in LArCV2 root files.

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

### Using the Module (LArCV1)

to be written


