from protojit import Serializer
import cPickle as pickle
import marshal
import json
from timeit import default_timer as now
import gc

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

matplotlib.rcParams['figure.figsize'] = (16, 5)
plt.rc("axes.spines", top=False, right=False)
sns.set_style('white')


def time(f, iters=10):
    gc.disable()
    start = now()
    for _ in range(iters):
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


def print_results(name, d):
    order = ['protojit', 'pickle', 'marshal', 'json']
    minv = min(d.values())
    ratios = [float(d[k]) / minv for k in order]
    for k in order:
        print('{}: {:.2f} ({})'.format(k, float(d[k]) / minv, d[k]))

    plt.title(name)
    plt.bar(order, ratios)
    # for rect, r in zip(plt.patches, ratios):
    #     plt.annotate(
    #         '{:.2f}'.format(r),
    #         xy=(rect.get_x() + rect.get_width() / 2, rect.get_height() + 5))


def main():
    values = [
        ('largelist', {'nums': list(range(100000))}),
        ('mixed', {
            'a': list(range(1000)),
            'b': 'hello',
            'c': 'foo' * 1000,
            'd': [{'a': 'b'} for _ in range(10000)]
        }),
        ('manyrecords', {
            'a': [
                {
                    'b': i,
                    'c': 'qq',
                    'e': i+2
                }
                for i in range(100000)
            ]
        }),
        ('manyfields', {
            'foo{}'.format(k): 1
            for k in range(10000)
        })
    ]  # yapf: disable

    # print('SIZE TESTS')
    # plt.clf()
    # for i, (k, v) in enumerate(values):
    #     plt.subplot(1, len(values), i + 1)
    #     print('== {} =='.format(k))
    #     print_results('size_' + k, size_test(v))
    # plt.savefig('benchmarks/size.png', dpi=300)
    # print('')

    # print('SERIALIZE TIME TESTS')
    # for (k, v) in values:
    #     print('== {} =='.format(k))
    #     print_results('serialize_' + k, serialize_time_test(v))
    # print('')

    print('DESERIALIZE TIME TESTS')
    for (k, v) in values:
        print('== {} =='.format(k))
        print_results('deserialize_' + k, deserialize_time_test(v))
    print('')


if __name__ == '__main__':
    main()
