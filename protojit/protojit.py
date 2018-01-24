from timeit import default_timer as now
import subprocess as sp
import tempfile
import struct
import shutil
import imp

class Timer:
    def __init__(self, s):
        self.s = s
        print('-- START: {}'.format(s))

    def __enter__(self):
        self.start = now()

    def __exit__(self, a, b, c):
        t = now() - self.start
        print('-- END: {:.3f} --'.format(t))



class ProtoType(object):
    def name(self):
        raise NotImplementedError

    def __str__(self):
        return self.name()


class TDouble(ProtoType):
    def name(self):
        return "double"


class TFloat(ProtoType):
    def name(self):
        return "float"


class TInt64(ProtoType):
    def name(self):
        return "int64"


class TInt32(ProtoType):
    def name(self):
        return "int32"


class TBool(ProtoType):
    def name(self):
        return "bool"


class TString(ProtoType):
    def name(self):
        return "string"


class TBytes(ProtoType):
    def name(self):
        return "bytes"


class TList(ProtoType):
    def __init__(self, elt_ty):
        self.elt_ty = elt_ty

    def name(self):
        return 'repeated {}'.format(self.elt_ty.name())


class TMessage(ProtoType):
    def __init__(self, field_tys):
        self.field_tys = field_tys
        self._name = None

    def name(self):
        return self._name


is_64bit = struct.calcsize('P') == 8
type_map = {
    float: TDouble() if is_64bit else TFloat(),
    int: TInt64() if is_64bit else TInt32(),
    bool: TBool(),
    str: TString(),
    bytes: TBytes()
}

SERIALIZER_COUNTER = 0


class Serializer(object):
    def __init__(self, obj):
        global SERIALIZER_COUNTER
        self._prefix = 'msg{}'.format(SERIALIZER_COUNTER)
        SERIALIZER_COUNTER += 1
        self._ty_counter = 0
        self._ty = self._typecheck(obj)
        assert isinstance(self._ty, TMessage)
        self._desc = self._make_descriptor(self._ty)

    def _typecheck(self, obj):
        ty = type(obj)
        if ty in type_map:
            return type_map[ty]
        else:
            if ty is list:
                assert len(obj) > 0
                return TList(self._typecheck(obj[0]))
            elif ty is dict:
                return TMessage(
                    {k: self._typecheck(v)
                     for k, v in obj.iteritems()})
            else:
                assert False

    def _gen_string(self, ty):
        if isinstance(ty, TMessage):
            name = '{}_{}'.format(self._prefix, self._ty_counter)
            ty._name = name
            self._ty_counter += 1

            number = {'_': 1}

            def field_str(k, fty):
                s = ''
                if isinstance(fty, TMessage):
                    msg_str = self._gen_string(fty)
                    s += msg_str
                elif isinstance(fty, TList) and isinstance(
                        fty.elt_ty, TMessage):
                    msg_str = self._gen_string(fty.elt_ty)
                    s += msg_str
                n = number['_']
                number['_'] += 1

                # "Field numbers 19000 through 19999 are reserved for the protocol buffer library
                # implementation."
                if number['_'] == 19000:
                    number['_'] = 20000

                return '{}\n{} {} = {};'.format(s, fty.name(), k, n)

            field_strs = [
                field_str(k, fty) for k, fty in ty.field_tys.iteritems()
            ]
            s = 'message {} {{ {} }}'.format(name, '\n'.join(field_strs))
            return s

    def _make_descriptor(self, ty):
        msg_str = self._gen_string(ty)

        out_dir = tempfile.mkdtemp()
        proto_path = '{}/{}.proto'.format(out_dir, self._prefix)
        with open(proto_path, 'w') as f:
            f.write('syntax = "proto3";\n{}'.format(msg_str))
        sp.check_call(
            'protoc --proto_path={} {} --python_out={}'.format(
                out_dir, proto_path, out_dir),
            shell=True)
        mod = imp.load_source('<proto>', '{}/{}_pb2.py'.format(
            out_dir, self._prefix))
        shutil.rmtree(out_dir)

        return getattr(mod, '{}_0'.format(self._prefix))

    def _serialize(self, desc, obj_ty, obj):
        for k, fty in obj_ty.field_tys.iteritems():
            if isinstance(fty, TMessage):
                self._serialize(getattr(desc, k), fty, obj[k])
            elif isinstance(fty, TList):
                if isinstance(fty.elt_ty, TMessage):
                    for v in obj[k]:
                        self._serialize(getattr(desc, k).add(), fty.elt_ty, v)
                else:
                    getattr(desc, k)[:] = obj[k]
            else:
                setattr(desc, k, obj[k])

    def dumps(self, obj):
        desc = self._desc()
        with Timer('To proto'):
            self._serialize(desc, self._ty, obj)
        with Timer('serialize'):
            x = desc.SerializeToString()
        return x

    def _deserialize(self, desc, obj_ty):
        obj = {}
        for k, fty in obj_ty.field_tys.iteritems():
            if isinstance(fty, TMessage):
                v = self._deserialize(getattr(desc, k), fty)
            elif isinstance(fty, TList):
                if isinstance(fty.elt_ty, TMessage):
                    v = [
                        self._deserialize(elt, fty.elt_ty)
                        for elt in getattr(desc, k)
                    ]
                else:
                    v = getattr(desc, k)[:]
            else:
                v = getattr(desc, k)
            obj[k] = v
        return obj

    def loads(self, s):
        desc = self._desc()
        desc.ParseFromString(s)
        return self._deserialize(desc, self._ty)

if __name__ == '__main__':
    x = {
            'a': [
                {
                    'b': 1,
                    'c': 'd',
                    'e': 'f'
                }
                for _ in range(100000)
            ]
        }
    print(len(Serializer(x).dumps(x)))
    import marshal
    import cPickle as pickle
    with Timer('marshal'):
        print(len(marshal.dumps(x)))
    with Timer('pickle'):
        print(len(pickle.dumps(x)))
    
