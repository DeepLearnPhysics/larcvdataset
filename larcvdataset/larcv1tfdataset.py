import os,sys
import tensorflow as tf
from tensorflow.python.framework import constant_op
from tensorflow.python.framework import dtypes

# Assumes the file is in the current working directory.
my_reader_dataset_module = tf.load_op_library(os.environ["LARCVDATASET_BASEDIR"]+"/lib/libLArCV1TFDatasetOp.so")

class LArCV1TFDataset(tf.data.Dataset):

  def __init__(self, filenames,producers,process_cfg):
    super(LArCV1TFDataset, self).__init__()
    # Create any input attrs or tensors as members of this class.
    if type(filenames) is str:
      self.filenames = [filenames]
    elif type(filenames) is not list:
      raise ValueError("filenames is not a list of strs")
    else:
      self.filenames = filenames
      
    if type(producers) is str:
      self.producers = [producers]
    elif type(producers) is not list:
      raise ValueError("producers is not a list of strs")
    else:
      self.producers = producers
      
    if type(process_cfg) is not str:
      raise ValueError("processor_cfg must be str with path to configuration file")
    else:
      self.process_cfg = process_cfg

    
  def _as_variant_tensor(self):
    # Actually construct the graph node for the dataset op.
    #
    # This method will be invoked when you create an iterator on this dataset
    # or a dataset derived from it.    
    return my_reader_dataset_module.larcv1tf_dataset(filenames=self.filenames, producers=self.producers, processor_cfg=self.process_cfg)

  # The following properties define the structure of each element: a scalar
  # <a href="../api_docs/python/tf/string"><code>tf.string</code></a> tensor. Change these properties to match the `output_dtypes()`
  # and `output_shapes()` methods of `larcv1tfDataset::Dataset` if you modify
  # the structure of each element.
  @property
  def output_types(self):
    if len(self.producers)>1:
      return len(self.producers)*(tf.float32,)
    else:
      return tf.float32

  @property
  def output_shapes(self):
    if len(self.producers)>1:
      return (tf.TensorShape([512,512,3]),)*len(self.producers)
    else:
      return tf.TensorShape([512,512,3])

  @property
  def output_classes(self):
    if len(self.producers)>1:
      return (tf.Tensor,)*len(self.producers)
    else:
      return tf.Tensor

if __name__ == "__main__":
  # Create a LArCV1TFDataset and print its elements.
  import cv2 as cv
  producerlist = ["wire","segment","ts_keyspweight"]
  with tf.Session() as sess:
    data = LArCV1TFDataset(["../../trainingdata/val.root"],producerlist,"test.cfg")
    iterator = data.make_one_shot_iterator()
    next_element = iterator.get_next()
    i = 0
    try:
      while True:
        print i        
        out = sess.run(next_element)
        for img,name in zip(out,producerlist):
          cv.imwrite( "%s_%d.png"%(name,i), img )
        #print(sess.run(next_element))  # Prints "LArCV1TFDataset!" ten times.
        i+=1
        if i>20:
          break
    except tf.errors.OutOfRangeError:
      pass
