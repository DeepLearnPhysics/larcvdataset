import os
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
    # print my_reader_dataset_module.__dict__
    # print help(my_reader_dataset_module)
    # print self.filenames, type(self.filenames)
    # filenames_op = constant_op.constant(self.filenames, dtypes.string)
    # print filenames_op
    
    return my_reader_dataset_module.larcv1tf_dataset(filenames=self.filenames, producers=self.producers, processor_cfg=self.process_cfg)
    #return my_reader_dataset_module.Larcv1tfDataset(filenames_op)

  # The following properties define the structure of each element: a scalar
  # <a href="../api_docs/python/tf/string"><code>tf.string</code></a> tensor. Change these properties to match the `output_dtypes()`
  # and `output_shapes()` methods of `larcv1tfDataset::Dataset` if you modify
  # the structure of each element.
  @property
  def output_types(self):
    return tf.string

  @property
  def output_shapes(self):
    return tf.TensorShape([])

  @property
  def output_classes(self):
    return tf.Tensor

if __name__ == "__main__":
  # Create a LArCV1TFDataset and print its elements.
  with tf.Session() as sess:
    iterator = LArCV1TFDataset(["val.root"],["adc"],"processor.cfg").make_one_shot_iterator()
    next_element = iterator.get_next()
    try:
      while True:
        print(sess.run(next_element))  # Prints "LArCV1TFDataset!" ten times.
    except tf.errors.OutOfRangeError:
      pass
