import os,sys

from larcvdataset import LArCV1Dataset

from larcv import larcv

if __name__ == "__main__":

    testfile = "/media/hdd1/larbys/ssnet_cosmic_retraining/cocktail/ssnet_retrain_cocktail_p01.root"
    productlist = [(larcv.kProductImage2D,"adc"),
                   (larcv.kProductImage2D,"label"),
                   (larcv.kProductImage2D,"weight")]

    io = LArCV1Dataset( testfile, productlist )
    data = io.getbatch( 5 )

    for d,array in data.items():
        print d,array.shape
