import os,sys,time

from larcvdataset import LArCV1Dataset
from larcvdataset import LArCV1PyTorchDataset

from larcv import larcv

if __name__ == "__main__":

    #testfile = "/media/hdd1/larbys/ssnet_cosmic_retraining/cocktail/ssnet_retrain_cocktail_p01.root"
    #productlist = [(larcv.kProductImage2D,"adc"),
    #               (larcv.kProductImage2D,"label"),
    #               (larcv.kProductImage2D,"weight")]

    if len(sys.argv)<=2:
        print "usage: python test_larcv1_image2d [larcv1 root file] [product list...]"
        print "example (using 2018-ssnet training data): python train00.root wire segment ts_keyspweight"
        sys.exit(0)
    
    testfile = sys.argv[1]
    products = sys.argv[2:]
    productlist = [ (larcv.kProductImage2D, x ) for x in products ]
    

    # if we use randomize it is much slower (can't take advantge of ROOT's neighboring entry caching
    io = LArCV1Dataset( testfile, productlist, randomize=True )

    tloop = time.time()
    batchsize = 5
    nbatches = 10
    for i in range(0,nbatches):
        data = io.getbatch( batchsize )
        for d,array in data.items():
            print d,array.shape
        print data["_rse_"]
    tloop = time.time()-tloop
    print "Time for test: %.2f secs (%.2f secs/batch)"%(tloop,tloop/nbatches)

    #iopytorch = LArCV1PyTorchDataset( testfile, productlist )
