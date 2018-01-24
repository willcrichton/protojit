from protojit import Serializer
import cPickle as pickle
import marshal
import json
from timeit import default_timer as now
import gc


def time(f):
    gc.disable()
    start = now()
    f()
    end = now() - start
    gc.enable()
    return end


def size_test(value):
    d = {
        'protojit': lambda: Serializer(value).dumps(value),
        'pickle': lambda: pickle.dumps(value),
        'marshal': lambda: marshal.dumps(value),
        'json': lambda: json.dumps(value)
    }
    return {k: len(v()) for k, v in d.iteritems()}


def serialize_time_test(value):
    s = Serializer(value)
    d = {
        'protojit': lambda: s.dumps(value),
        'pickle': lambda: pickle.dumps(value),
        'marshal': lambda: marshal.dumps(value),
        'json': lambda: json.dumps(value)
    }
    return {k: time(v) for k, v in d.iteritems()}


def deserialize_time_test(value):
    s = Serializer(value)
    s1 = s.dumps(value)
    s2 = pickle.dumps(value)
    s3 = marshal.dumps(value)
    s4 = json.dumps(value)
    d = {
        'protojit': lambda: s.loads(s1),
        'pickle': lambda: pickle.loads(s2),
        'marshal': lambda: marshal.loads(s3),
        'json': lambda: json.loads(s4)
    }
    return {k: time(v) for k, v in d.iteritems()}


def print_results(d):
    order = ['protojit', 'pickle', 'marshal', 'json']
    for k in order:
        print('{}: {}'.format(k, d[k]))


def main():
    values = [
        ('largelist', {'nums': list(range(100000))}),
        ('mixed', {
            'a': list(range(1000)),
            'b': 'hello',
            'c': 'foo' * 1000,
            'd': [{'a': 'b'} for _ in range(10000)]
        }),
        ('manyfields', {
            'foo{}'.format(k): 1
            for k in range(100000)
        })
    ]  # yapf: disable

    print('SIZE TESTS')
    for (k, v) in values:
        print('== {} =='.format(k))
        print_results(size_test(v))
    print('')

    print('SERIALIZE TIME TESTS')
    for (k, v) in values:
        print('== {} =='.format(k))
        print_results(serialize_time_test(v))
    print('')

    print('DESERIALIZE TIME TESTS')
    for (k, v) in values:
        print('== {} =='.format(k))
        print_results(deserialize_time_test(v))
    print('')


if __name__ == '__main__':
    main()
