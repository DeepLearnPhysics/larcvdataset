import os,sys
from collections import OrderedDict
import ROOT as rt
from larcv import larcv
import numpy as np

# Data interface to LArCV1. Simple interface. No threading. Used for deploy.
class LArCV1Dataset:
    def __init__(self, inputfile, products, store_eventids=False, randomize=False ):

        # inputs
        # cfgfile: path to configuration. see test.py.ipynb for example of configuration
        self.inputfiles = []
        if type(inputfile) is str:
            self.inputfiles.append( inputfile )
        elif type(inputfile) is list:
            self.inputfiles = inputfile
        else:
            raise ValueError("LArCV1Dataset inputfile variable should be str or list. is {}".format(type(inputfile)))

        if type(products) is not list:
            raise ValueError("LArCV1Dataset 'products' variable should be a list with (product type,tree name)")
        self.products = products

        self.store_eventids = store_eventids
        self.randomize = randomize

        self.io = larcv.IOManager( larcv.IOManager.kREAD )
        for f in self.inputfiles:
            self.io.add_in_file( f )
        self.io.initialize()

        self.nentries = self.io.get_n_entries()

        # batch info, not set until later
        self._batch_size = None

        self.current_entry = 0
        self.delivered = 0
        self.permuted = None
        return
              
    def getbatch(self, batchsize):

        if self._batch_size is None:
            self._batch_size = batchsize
        else:
            # should be careful about setting batch sizes
            self._batch_size = batchsize
            
        # get entry indices of batch
        if self.randomize:
            if self.delivered+self._batch_size>=self.nentries:
                # refresh the permutated event indices
                self.permuted = np.random.permutation( self.nentries )
                # reset the delivered count
                self.delivered = 0
            indices = self.permuted[self.delivered:self.delivered+self._batch_size]
            
        else:
            # sequential
            if self.delivered+self._batch_size>=self.nentries or self.permuted is None:
                self.permuted = np.arange( self.nentries, dtype=np.int )
                self.delivered = 0
        
        batch_products = {}
        batch_products["_rse_"] = np.zeros( (self._batch_size, 3), dtype=np.int )
        indices = self.permuted[self.delivered:self.delivered+self._batch_size]
        for i,index in enumerate(indices): 

            
            data = self.__getitem__(index)

            # now we convert and organize the data products
            for n,(ktype,producer_name) in enumerate(self.products):
                if producer_name not in batch_products:
                    # make entry for this
                    entry_arr = data[n]
                    batch_arr = np.zeros( (self._batch_size,)+entry_arr.shape, dtype=entry_arr.dtype )
                    batch_products[(ktype,producer_name)] = batch_arr
                batch_products[(ktype,producer_name)][i,:] = entry_arr[:]
            for ii in range(3):
                batch_products["_rse_"][i,ii] = self.rse[ii]
        
        return batch_products

    def __getitem__(self,index):
        
        # have io read entry
        self.io.read_entry( index )
        
        # now we convert and organize the data products
        numpy_arrays = OrderedDict()
        self.rse = None
        for ktype,producer_name in self.products:
            try:
                ev_data = self.io.get_data( ktype, producer_name )
            except:
                raise RuntimeError("could not retrieve data product for product_id=%d and producername=%s"%(ktype,producer_name))
            if self.rse is None:
                self.rse = ( ev_data.run(), ev_data.subrun(), ev_data.event() )
            

            # handle different data product types
            if ktype==larcv.kProductImage2D:
                img_v = ev_data.Image2DArray()
                img_np = np.zeros( (img_v.size(),img_v[0].meta().cols(),img_v[0].meta().rows()), dtype=np.float32 )
                for iimg in range(img_v.size()):
                    img_np[iimg,:] = larcv.as_ndarray( img_v[iimg] )[:]
                numpy_arrays[(ktype,producer_name)] = img_np
            else:
                raise RuntimeError("product,\"{}\", not yet supported. please support it by adding it here.".format(ktype))

        output = []
        for k,v in numpy_arrays.items():
            output.append(v)

        return output
