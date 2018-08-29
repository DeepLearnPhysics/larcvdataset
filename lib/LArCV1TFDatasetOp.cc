#include <sys/stat.h>
#include <vector>
#include <string>
#include "tensorflow/core/framework/common_shape_fns.h"
#include "tensorflow/core/framework/dataset.h"
#include "tensorflow/core/framework/op.h"
#include "tensorflow/core/framework/shape_inference.h"
#include "tensorflow/core/lib/io/buffered_inputstream.h"
#include "tensorflow/core/platform/file_system.h"

#include "Processor/ProcessDriver.h"
#include "DataFormat/EventImage2D.h"
#include "DataFormat/Image2D.h"


namespace larcv1dataset {
  //  namespace {
  
  using ::std::string;
  using ::tensorflow::Tensor;
  using ::tensorflow::TensorShape;
  using ::tensorflow::DataType;  
  using ::tensorflow::DT_STRING;
  using ::tensorflow::DT_FLOAT;  
  using ::tensorflow::PartialTensorShape;
  using ::tensorflow::Status;

  class Larcv1tfDatasetOp : public tensorflow::DatasetOpKernel {
  public:
      
    Larcv1tfDatasetOp(tensorflow::OpKernelConstruction* ctx) : DatasetOpKernel(ctx) {
      // Parse and validate any attrs that define the dataset using
      // `ctx->GetAttr()`, and store them in member variables.
      OP_REQUIRES_OK(ctx,ctx->GetAttr("filenames", &_filenames));
      OP_REQUIRES_OK(ctx,ctx->GetAttr("producers", &_producers));
      OP_REQUIRES_OK(ctx,ctx->GetAttr("processor_cfg", &_processor_cfg));
    };

    void MakeDataset(tensorflow::OpKernelContext* ctx,
		     tensorflow::DatasetBase** output) override {
      // Parse and validate any input tensors that define the dataset using
      // `ctx->input()` or the utility function
      // `ParseScalarArgument<T>(ctx, &arg)`.
      // Create the dataset object, passing any (already-validated) arguments from
      // attrs or input tensors.
      *output = new Dataset(ctx, _filenames, _producers, _processor_cfg);
    };

  private:
      
    class Dataset : public tensorflow::GraphDatasetBase {
    public:
      Dataset(tensorflow::OpKernelContext* ctx,
	      const std::vector<std::string>& filenames,
	      const std::vector<std::string>& producers,
	      const std::string& cfg )
	: GraphDatasetBase(ctx), _filenames(filenames), _producers(producers), _processor_cfg(cfg), _plarcv_processor(nullptr) {
	_plarcv_processor = new larcv::ProcessDriver( _processor_cfg );
	_plarcv_processor->override_input_file( _filenames );
	_plarcv_processor->initialize();
	_plarcv_processor->process_entry();// process first entry

	larcv::IOManager& io = _plarcv_processor->io_mod();	  	  
	for ( auto& producer : _producers ) {
	  larcv::EventImage2D* evdata = (larcv::EventImage2D*)io.get_data( larcv::kProductImage2D, producer );
	  const std::vector<larcv::Image2D>& img_v = evdata->Image2DArray();
	  int nchs = img_v.size();
	  // image2d, outer dim is cols
	  int rows = img_v.front().meta().rows();
	  int cols = img_v.front().meta().cols();
	  PartialTensorShape shape( {cols,rows,nchs} );
	  _output_shapes.push_back( shape );
	}
      }


      virtual ~Dataset() {
      	// destroy the processor
      	_plarcv_processor->finalize();
      	delete _plarcv_processor;
      };
      
      std::unique_ptr<tensorflow::IteratorBase> MakeIteratorInternal(const string& prefix) const override {
	return std::unique_ptr<tensorflow::IteratorBase>(new Iterator({this, tensorflow::strings::StrCat(prefix, "::Larcv1tf")}));
      }

      
      // Record structure: Each record is represented by a scalar string tensor.
      //
      // Dataset elements can have a fixed number of components of different
      // types and shapes; replace the following two methods to customize this
      // aspect of the dataset.
      const tensorflow::DataTypeVector& output_dtypes() const override {
	int ntensors = _producers.size();
	tensorflow::DataTypeVector dd(ntensors);
	for ( int i=0; i<ntensors; i++)
	  dd[i] = DT_FLOAT;
	static auto* const dtypes = new tensorflow::DataTypeVector( dd );
	return *dtypes;
      }
      const std::vector<PartialTensorShape>& output_shapes() const override {
	static std::vector<PartialTensorShape>* shapes =
	  new std::vector<PartialTensorShape>( _output_shapes  );
	return *shapes;
      }

      string DebugString() const override { return "Larcv1tfDatasetOp::Dataset"; }

    protected:
      // Optional: Implementation of `GraphDef` serialization for this dataset.
      //
      // Implement this method if you want to be able to save and restore
      // instances of this dataset (and any iterators over it).
      Status AsGraphDefInternal(DatasetGraphDefBuilder* b,
				tensorflow::Node** output) const override {
	// Construct nodes to represent any of the input tensors from this
	// object's member variables using `b->AddScalar()` and `b->AddVector()`.

	std::vector<tensorflow::Node*> input_tensors;
	TF_RETURN_IF_ERROR(b->AddDataset(this, input_tensors, output));
	
	return Status::OK();
      }

    private:
      class Iterator : public tensorflow::DatasetIterator<Dataset> {
      public:
        explicit Iterator(const Params& params) : DatasetIterator<Dataset>(params), i_(0) {}
	  

	// Implementation of the reading logic.
	//
	// The example implementation in this file yields the string "MyReader!"
	// ten times. In general there are three cases:
	//
	// 1. If an element is successfully read, store it as one or more tensors
	//    in `*out_tensors`, set `*end_of_sequence = false` and return
	//    `Status::OK()`.
	// 2. If the end of input is reached, set `*end_of_sequence = true` and
	//    return `Status::OK()`.
	// 3. If an error occurs, return an error status using one of the helper
	//    functions from "tensorflow/core/lib/core/errors.h".
        Status GetNextInternal(tensorflow::IteratorContext* ctx,
			       std::vector<tensorflow::Tensor>* out_tensors,
			       bool* end_of_sequence) override {
	  // NOTE: `GetNextInternal()` may be called concurrently, so it is
	  // recommended that you protect the iterator state with a mutex.

	  tensorflow::mutex_lock l(mu_);	  
	  
	  // we get the list of items from the _producers list
	  // get next entry
	  larcv::IOManager& io = dataset()->_plarcv_processor->io_mod();	  
	  bool ok = dataset()->_plarcv_processor->process_entry();

	  for (int ip=0; ip<(int)dataset()->_producers.size(); ip++) {
	    std::string producer = dataset()->_producers[ip];
	    larcv::EventImage2D* evdata = (larcv::EventImage2D*)io.get_data( larcv::kProductImage2D, producer );
	    const std::vector<larcv::Image2D>& img_v = evdata->Image2DArray();
	    int nchs = img_v.size();
	    // image2d, outer dim is cols
	    int rows = img_v.front().meta().rows();
	    int cols = img_v.front().meta().cols();
	    tensorflow::Tensor tensor( ctx->allocator({}), DT_FLOAT, TensorShape( {cols,rows,nchs} ) );
	    auto flat = tensor.flat<float>();
	    for ( int ic=0; ic<nchs; ic++ ) {
	      const std::vector<float>& vec = img_v[ic].as_vector();
	      for (int icol=0; icol<cols; icol++) {
		for (int irow=0; irow<rows; irow++)
		  flat( icol*rows*nchs + irow*nchs + ic ) = vec[icol*rows + irow]; // this sucks
	      }
	    }
	    out_tensors->emplace_back( std::move(tensor) );
	  }	    
	  if (i_ < 10) {
	    //   // Create a scalar string tensor and add it to the output.
	    //   tensorflow::Tensor record_tensor(ctx->allocator({}), DT_STRING, {});
	    //   record_tensor.scalar<string>()() = "Larcv1tf!";
	    //   out_tensors->emplace_back(std::move(record_tensor));
	    ++i_;
	    *end_of_sequence = false;
	  } else {
	    *end_of_sequence = true;
	  }
	  return Status::OK();
	}

      protected:
	// Optional: Implementation of iterator state serialization for this
	// iterator.
	//
	// Implement these two methods if you want to be able to save and restore
	// instances of this iterator.
	Status SaveInternal(tensorflow::IteratorStateWriter* writer) override {
	  tensorflow::mutex_lock l(mu_);
	  TF_RETURN_IF_ERROR(writer->WriteScalar(full_name("i"), i_));
	  return Status::OK();
	}
	Status RestoreInternal(tensorflow::IteratorContext* ctx,
			       tensorflow::IteratorStateReader* reader) override {
	  tensorflow::mutex_lock l(mu_);
	  TF_RETURN_IF_ERROR(reader->ReadScalar(full_name("i"), &i_));
	  return Status::OK();
	}

      private:
	tensorflow::mutex mu_;
	tensorflow::int64 i_ GUARDED_BY(mu_);
      };// end of class Iterator : public tensorflow::DatasetIterator<Dataset>

    protected:
      // internal data members
      std::vector<std::string> _filenames; // input filenames
      std::vector<std::string> _producers; // name of image2d trees to grab tensors from      
      std::string              _processor_cfg; // process driver name
      larcv::ProcessDriver*    _plarcv_processor; // process driver instance
      std::vector< PartialTensorShape > _output_shapes;
    };// end of class Dataset : public tensorflow::GraphDatasetBase

  protected:
    // internal data members
    std::vector<std::string>  _filenames; // input filenames
    std::vector<std::string>  _producers; // name of image2d trees to grab tensors from      
    std::string               _processor_cfg; // process driver name

  };//class Larcv1tfDatasetOp : public tensorflow::DatasetOpKernel

// Register the op definition for Larcv1tfDataset.
//
// Dataset ops always have a single output, of type `variant`, which represents
// the constructed `Dataset` object.
//
// Add any attrs and input tensors that define the dataset here.
REGISTER_OP("Larcv1tfDataset")
    .Attr("filenames: list(string)")
    .Attr("processor_cfg: string")
    .Attr("producers: list(string)")
    .Output("handle: variant") 
    .SetIsStateful()
    .SetShapeFn(tensorflow::shape_inference::ScalarShape);

// Register the kernel implementation for MyReaderDataset.
REGISTER_KERNEL_BUILDER(Name("Larcv1tfDataset").Device(tensorflow::DEVICE_CPU),
			Larcv1tfDatasetOp);
			  
  //}  // namespace
}  // namespace larcv1dataset

