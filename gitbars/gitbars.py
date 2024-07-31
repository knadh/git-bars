#!/usr/bin/python

"""
git-bars produces a simple commit visualisation for a git repository.

git-bars is a Python utility that uses 'git log'
to produce a simple bar graph visualisation for
commit activity in a git repository.

Kailash Nadh, https://nadh.in

Licensed under the MIT License.
"""

import sys
import argparse
import datetime
from subprocess import check_output
from collections import OrderedDict, namedtuple

import pkg_resources
__version__ = pkg_resources.require("git-bars")[0].version


Item = namedtuple(
    "Item", ["timestamp", "is_weekend", "author", "commits", "score"])
Item.__new__.__defaults__ = (None, False, "none", 0, 0)


def print_bars(items, block=u"\u2580", width=50):
    """Print unicode bar representations of dates and scores."""
    for i in items:
        num = str(items[i].commits)

        sys.stdout.write(i)
        sys.stdout.write("  ")
        sys.stdout.write(num)
        sys.stdout.write((5 - len(num)) * " ")

        # Colour the weekend bars.
        if items[i].is_weekend:
            sys.stdout.write("\033[94m")

        sys.stdout.write(block * int(items[i].score * width))

        if items[i].is_weekend:
            sys.stdout.write("\x1b[0m")

        sys.stdout.write("\n")


def filter(items, periodicity="day", author=""):
    """Filter entries by periodicity and author."""
    bars = OrderedDict()

    for i in items:
        # Extract the day/month/year part of the date.
        d = i.timestamp
        if periodicity == "week":
            label = d.strftime("%Y/%V")
        elif periodicity == "month":
            label = d.strftime("%Y-%m")
        elif periodicity == "year":
            label = d.strftime("%Y")
        else:
            label = d.strftime("%Y-%m-%d %a")

        # Filter by author.
        if author != "":
            if author not in i.author:
                continue

        if label not in bars:
            bars[label] = Item(*i)
        else:
            bars[label] = bars[label]._replace(
                commits=bars[label].commits + i.commits)

    return bars


def get_scores(items):
    """Compute normalized scores (0-1) for commit numbers."""
    vals = [items[i].commits for i in items]
    vals.append(0)

    xmin = min(vals)
    xmax = max(vals)

    # Normalize.
    out = OrderedDict()
    for i in items:
        out[i] = Item(
            *(items[i]))._replace(score=normalize(items[i].commits, xmin, xmax))

    return out


def get_log(repo, after, before, reverse=False, fill=False):
    """Return the list of git log from the git log command."""
    # 2018-01-01 00:00:00|author@author.com
    args = ["git", "log", "--pretty=format:%ai|%ae", "--reverse"]
    if repo:
        args = [args[0]] + ["-C", f'{repo}'] + args[1:]

    if after:
        args.append("--after=%s" % (after,))
    if before:
        args.append("--before=%s" % (before,))

    items = []
    for o in check_output(args, universal_newlines=True, shell=False).split("\n"):
        c = o.split("|")
        t = datetime.datetime.strptime(c[0], "%Y-%m-%d %H:%M:%S %z")
        items.append(
            Item(timestamp=t, author=c[1], is_weekend=t.weekday() > 4, commits=1))

    if fill:
        fill_dates(items)

    if not reverse:
        items.reverse()

    return items


def normalize(x, xmin, xmax):
    """Normalize a number to a 0-1 range given a min and max of its set."""
    return float(x - xmin) / float(xmax - xmin)


def fill_dates(data):
    """Fill missing dates where there were no commits."""
    n = len(data)
    i = 0
    while i < n - 1:
        cur = data[i].timestamp
        if (data[i+1].timestamp - cur).days > 1:
            data.insert(i+1, Item(
                timestamp=cur + datetime.timedelta(days=1),
                is_weekend=cur.weekday() > 4
            ))
            n += 1
        i += 1


def main():
    """Commandline entry point."""
    p = argparse.ArgumentParser(description="Shows git commit count bars. "
                                "Weekends are coloured. (version " + __version__ + ")")
    p.add_argument("-p", "--periodicity", action="store", dest="periodicity",
                   type=str, required=False, default="month",
                   choices=["day", "week", "month", "year"])

    p.add_argument("-u", "--author", action="store", dest="author",
                   type=str, required=False, default="",
                   help="filter by author's e-mail (substring)")

    p.add_argument("-a", "--after", action="store", dest="after",
                   type=str, required=False, default="",
                   help="after date (yyyy-mm-dd hh:mm)")

    p.add_argument("-b", "--before", action="store", dest="before",
                   type=str, required=False, default="",
                   help="before date (yyyy-mm-dd hh:mm)")

    p.add_argument("-r", "--reverse", action="store", dest="reverse",
                   type=bool, required=False, default=False,
                   help="reverse date order")

    p.add_argument("-f", "--fill", action="store", dest="fill",
                   type=bool, required=False, default=False,
                   help="fill dates (with no commits) on the graph")

    p.add_argument("repo", type=str, nargs='?', default="",
                   help="Path to a git repository")

    args = p.parse_args()

    """Invoke the utility."""
    items = []
    try:
        items = get_log(args.repo, args.after, args.before, args.reverse,
                        args.fill)
    except Exception as e:
        print("error running 'git log': %s" % (e,))
        return

    filtered = filter(items, args.periodicity, args.author)

    scores = get_scores(filtered)
    if scores:
        print("%d commits over %d %s(s)" %
              (sum([filtered[f].commits for f in filtered]),
               len(scores),
               args.periodicity))
        print_bars(scores)
    else:
        print("No commits to plot")


if __name__ == "__main__":
    main()
