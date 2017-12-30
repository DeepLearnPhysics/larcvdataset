# larcvdataset

This module defines a concrete instance of the pytorch Dataset class. It serves as an interface to data stored in LArCV2 root files.

This module assumes

* ROOT6: LArCV2's primary dependency
* numpy: an optional LArCV2 dependency but necessary for LArCV2's python interface
* LArCV2 is built and the proper environment variables have been setup (via configure.sh)

## Example script

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



