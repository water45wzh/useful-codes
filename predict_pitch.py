#!/usr/bin/env python

import re
import math
import argparse

spliter = re.compile('\s+')

def get_arguments():
    parser = argparse.ArgumentParser(description='predict pitch')
    parser.add_argument('--input', type=str, default=None, required=True,
                        help='input pitch file, the 1st column is F0')
    parser.add_argument('--output', type=str, default=None, required=True,
                        help='output normalized F0 file')

    return parser.parse_args()


def main():
    args = get_arguments()

    raw_f0 = []
    with open(args.input, 'r') as f:
        for line in f:
            line = spliter.split(line)
            raw_f0.append(float(line[0]))

    vo_id = [0]
    j = 0
    for f0 in raw_f0:
        if f0 > 20:
            vo_id.append(j)

        j += 1

    sen_len = len(raw_f0)
    vo_id.append(sen_len)
    vo_len = len(vo_id)

    if vo_len > 0:
        f0_m = sum(raw_f0) / (vo_len - 2.0)  # origin the number is @vo_id
        inf0 = raw_f0[:]  # Inter_F0
        inf0[0] = f0_m  #? why
        inf0.append(f0_m)

        for j in range(0, vo_len - 1):
            ps = vo_id[j+1] - vo_id[j] + 1
            if ps < 3:
                continue

            diff = inf0[vo_id[j]] - inf0[vo_id[j+1]]
            x = range(1, ps + 1)
            y = []
            if diff > 1e-3:
                sf = math.log(diff) / ps
                x = list(reversed(x))
                for k in range(0, ps):
                    y.append(math.exp(sf * x[k]) + inf0[vo_id[j+1]])
            elif diff < -1e-3:
                sf = math.log(-diff) / ps
                for k in range(0, ps):
                    y.append(math.exp(sf * x[k]) + inf0[vo_id[j]])
            else:
                for k in range(0, ps):
                    y.append(inf0[vo_id[j]])

            h = 0
            for m in range(vo_id[j] + 1, vo_id[j+1]):
                inf0[m] = y[h]
                h += 1

    # smoothing using FIR filter
    no = 12  # order = 11
    b = (0.003261, 0.0076237, -0.022349, -0.054296, 0.12573, 0.44003, 0.44003, 0.12573, -0.054296, -0.022349, 0.0076237, 0.003261)

    # 0..0 xxx 0..0
    z = [inf0[0]] * no
    for j in range(len(inf0) - 1):
        z.append(inf0[j])

    for j in range(no):
        z.append(inf0[-2])

    # y(n) = b(1)*x(n) + b(2)*x(n-1) + ... + b(nb+1)*x(n-nb) - a(2)*y(n-1) - ... - a(na+1)*y(n-na)
    inf0s = []
    for i in range(len(inf0) + no - 1):
        conv = .0
        for j in range(no):
            conv += z[i + no - j] * b[j]

        inf0s.append(conv)

    # discard 0 ~ no/2 and last-no/2 ~ last, remain number: @inf0 - 1
    with open(args.output, 'w') as f:
        idx = 0
        for f0 in inf0s:
            if idx >= no / 2 and idx < len(inf0) + no / 2 - 1:
                f.write("%.2f\n" % f0)

            idx += 1


if __name__ == '__main__':
    main()
