from collections import Counter
import json
import random

import numpy as np

from easylogging import *


def markov_song(a, max_consective_zeros=16):
    new_a = ','.join(str(x) for x in a)
    while '0,' * (max_consective_zeros + 1) in new_a:
        new_a = new_a.replace('0,' * (max_consective_zeros + 1),
                              '0,' * (max_consective_zeros))
    a = map(int, new_a.split(','))
    num_to_index = {}
    index_to_num = {}
    b = []
    for num in a:
        if num not in num_to_index:
            index = len(index_to_num)
            index_to_num[index] = num
            num_to_index[num] = index
        b.append(num_to_index[num])

    m = np.zeros((len(num_to_index), len(num_to_index)))
    for (x, y), c in Counter(zip(b, b[1:])).items():
        m[x, y] = c

    for i, row in enumerate(m):
        total = np.sum(row)
        if total == 0:
            continue
        for j, val in enumerate(row):
            m[i][j] = val / total

    markov_pattern = [random.choice(list(index_to_num.keys()))]
    for i in range(1, 100):
        r = random.random()
        possibilities = np.cumsum(m[markov_pattern[i - 1]])
        for j, val in enumerate(possibilities):
            if r < val:
                markov_pattern.append(j)
                break
        markov_pattern.append(j)
    new_song = markov_pattern
    for i, n in enumerate(new_song):
        new_song[i] = index_to_num[n]

    return new_song

# a = json.load(open('states.json', 'r'))
# song = markov_song(a)
# with open('state2.json', 'w') as f:
#     f.write(json.dumps(song))
# print(song)
