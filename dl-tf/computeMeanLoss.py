#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import numpy as np
import matplotlib.pyplot as plt 
import argparse

AVERAGE_STEPS = 1000

Tag = 'loss = '
Step_tag = 'step '
regex = r'step[\s](\d{1,}).{1,}loss[\s]=[\s](\d{1,}\.\d{1,})'


def get_arguments():
    parser = argparse.ArgumentParser(description='Mean Loss Tool')
    parser.add_argument('--input_file', type=str, default=None,
                        help='input file to compute the mean loss.')
    parser.add_argument('--average_steps', type=int, default=AVERAGE_STEPS,
                        help='how many steps to compute mean loss')
    parser.add_argument('--output_file', type=str, default='average_loss.txt',
                        help='how many steps to compute mean loss')

    return parser.parse_args()


def main():
    args = get_arguments()
    if args.input_file is None:
        print("input_file should not be None")
        return

    steps = []
    losses = []
    with open(args.input_file) as f:
        for line in f:
            # idx = line.find(Tag)
            # if idx == -1:
            #     continue

            # idx2 = line.find(',')
            # loss = line[len(Tag) + idx : idx2]
            # loss = float(loss)

            # idx = line.find(Step_tag)
            # idx2 = line.find(' - loss')
            # step = line[len(Step_tag) + idx : idx2]

            # steps.append(step)
            # losses.append(loss)

            ## regex version

            matches = re.search(regex, line)
            if matches:
                step = matches.group(1)
                loss = matches.group(2)
                step = int(step)
                loss = float(loss)
                steps.append(step)
                losses.append(loss)

    # plot loss curve
    plt.xlabel('steps')
    plt.ylabel('loss')
    plt.title('Wavenet Loss')
    plt.plot(steps, losses, linewidth=2.0)
    plt.savefig('loss.png')
    print("loss curve picture is saved as loss.png")
    # plt.show()

    # compute average loss by --average_steps
    AVERAGE_STEPS = args.average_steps
    print('compute mean loss every %d steps' % AVERAGE_STEPS)
    step = 0
    mean_losses = []
    while step < len(steps):
        if step + AVERAGE_STEPS <= len(steps):
            sub_losses = losses[step:step+AVERAGE_STEPS]
        else:
            sub_losses = losses[step:]

        mean_loss = sum(sub_losses) / len(sub_losses)
        mean_losses.append(mean_loss)
        step += AVERAGE_STEPS

    output = open(args.output_file, 'w')
    step = 0
    for loss in mean_losses:
        step += AVERAGE_STEPS
        output.write('step %d, loss = %f \n' % (step, loss))

    output.flush()
    output.close()
    print("job done!")
    print("Averaged loss saved as %s" % args.output_file)


if __name__ == '__main__':
    main()
