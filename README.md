# protojit

Protojit is a small library for automatic serialization and deserialization (akin to `pickle`, `marshal`, and `json`) of Python data objects. It uses Protobuf to dynamically JIT compile a serializer for a given kind of data. Essentially, it typechecks an example of what your data looks like and generates the appropriate serializer for that type.

While this proof of concept works correctly, upon benchmarking, this library was not any faster during serialization or deserialization than `marshal`, so it did not succeed in the goal of being the fastest serializer. It does, however, generate files that are on average 2-4x smaller than the aforementioned comparison libraries (try running `bench.py`).
