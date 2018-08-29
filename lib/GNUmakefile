CXX      =  g++

CFLAGS   =   -g -fPIC -m64 -std=c++11
CFLAGS   += `root-config --cflags`
CFLAGS   += -DNDEBUG

INCLUDES =  `root-config --incdir`
INCLUDES += `larlite-config --includes`
INCLUDES += `larcv-config --includes`
INCLUDES += -I/usr/local/lib/python2.7/dist-packages/tensorflow/include

LDFLAGS  =  `root-config --ldflags` -lstdc++
LDLIBS   =  `root-config --libs`
LDLIBS   += `larlite-config --libs`
LDLIBS   += `larcv-config --libs`
LDLIBS   += -L/usr/local/lib/python2.7/dist-packages/tensorflow -ltensorflow_framework

LIB = libLArCV1TFDatasetOp.so


all: $(LIB)

%.o: %.cc
	@echo "<< compiling $@ >>"
	$(CXX) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(LIB): LArCV1TFDatasetOp.o
	$(CXX) -shared $(LDFLAGS) -o $@ $^ $(LDLIBS)

clean:
	@rm *.so *.o
