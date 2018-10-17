import os,sys,time

from larcvdataset.larcvserver import LArCVServer

def load_data( io ):
    """ example of data loader function. we provide dictionary with numpy arrays (no batch) """
    from larcv import larcv
    import numpy as np
    
    width  = 832
    height = 512
    src_adc_threshold = 10.0

    index = (1,0)
    products = ["source","targetu","targetv","flowy2u","flowy2v","visiy2u","visiy2v","meta"]
    data = {}
    for k in products:
        if k !="meta":
            data[k] = np.zeros( (1,width,height), dtype=np.float32 )
        else:
            data[k] = np.zeros( (3,width,height), dtype=np.float32 )            
        
    ev_adc = io.get_data("image2d","adc")
    ev_flo = io.get_data("image2d","pixflow")
    ev_vis = io.get_data("image2d","pixvisi")

    data["source"][0,:,:]  = larcv.as_ndarray( ev_adc.as_vector()[2] ).transpose(1,0)
    data["targetu"][0,:,:] = larcv.as_ndarray( ev_adc.as_vector()[0] ).transpose(1,0)
    data["targetv"][0,:,:] = larcv.as_ndarray( ev_adc.as_vector()[1] ).transpose(1,0)

    data["flowy2u"][0,:,:] = larcv.as_ndarray( ev_flo.as_vector()[0] ).transpose(1,0)
    data["flowy2v"][0,:,:] = larcv.as_ndarray( ev_flo.as_vector()[1] ).transpose(1,0)

    data["visiy2u"][0,:,:] = larcv.as_ndarray( ev_vis.as_vector()[0] ).transpose(1,0)
    data["visiy2v"][0,:,:] = larcv.as_ndarray( ev_vis.as_vector()[1] ).transpose(1,0)

    for ip in xrange(0,3):
        data["meta"][ip,0,0] = ev_adc.as_vector()[ip].meta().min_x()
        data["meta"][ip,0,1] = ev_adc.as_vector()[ip].meta().min_y()
        data["meta"][ip,0,2] = ev_adc.as_vector()[ip].meta().max_x()
        data["meta"][ip,0,3] = ev_adc.as_vector()[ip].meta().max_y()
            
    return data
    

if __name__ == "__main__":

    batchsize = 4
    nworkers  = 4
    print "start feeders"
    inputfile = "../testdata/smallsample/larcv_dlcosmictag_5482426_95_smallsample082918.root"
    feeder = LArCVServer(batchsize,"test",load_data,inputfile,nworkers,server_verbosity=0,worker_verbosity=0)

    print "wait for workers to load up"
    twait = 3
    while twait>0:
        time.sleep(0.5)
        twait -= 1
        print "twait: ",twait
    
    print "start receiving"
    nentries = 50
    tstart = time.time()
    for n in xrange(nentries):
        batch = feeder.get_batch_dict()
        print "entry[",n,"] from ",batch["feeder"],": ",batch.keys()
    tend = time.time()-tstart
    print "elapsed time, ",tend,"secs ",tend/float(nentries)," sec/batch"
