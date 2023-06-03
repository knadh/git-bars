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
from collections import OrderedDict
from colorama import Fore, Style

import pkg_resources
__version__ = pkg_resources.require("git-bars")[0].version

# Define the colors for each weekday
colors = {
    "Monday": Fore.RED,
    "Tuesday": Fore.GREEN,
    "Wednesday": Fore.YELLOW,
    "Thursday": Fore.BLUE,
    "Friday": Fore.MAGENTA,
    "Saturday": Fore.CYAN,
    "Sunday": Fore.WHITE
}

def print_bars(items, periodicity, colorize, block=u"\u2580", width=50):
    """Print unicode bar representations of dates and scores."""
    if periodicity == "day":
        # Get the first and last elements of the array
        first_date = next(iter(items))
        last_date = next(reversed(items))

        max_day_name_length = max(len(datetime.datetime.strptime(i[:10], "%Y-%m-%d").strftime("%A")) for i in items)

        # Iterate through every date between the first and last dates
        current_date = last_date
        while current_date <= first_date:
            if current_date in items:
                item = items[current_date]
                num = str(item["commits"])
            else:
                num = "0"

            date_string = current_date
            day_name = datetime.datetime.strptime(date_string, "%Y-%m-%d").strftime("%A")

            # Choose the color based on the weekday
            color = colors[day_name]

            if colorize:
                sys.stdout.write(color)
                sys.stdout.write(Style.BRIGHT)

            sys.stdout.write(date_string)
            sys.stdout.write("  ")
            sys.stdout.write(day_name.ljust(max_day_name_length))
            sys.stdout.write("  ")
            sys.stdout.write(num)
            sys.stdout.write((5 - len(num)) * " ")

            # Colour the weekend bars.
            if current_date in items and items[current_date]["weekend"]:
                sys.stdout.write("\033[94m")

            sys.stdout.write(block * int(items.get(current_date, {"score": 0})["score"] * width))

            if current_date in items and items[current_date]["weekend"]:
                sys.stdout.write("\x1b[0m")

            sys.stdout.write("\n")

            if (day_name == "Sunday"):
                sys.stdout.write("\n")

            # Move to the next date
            curr_date = datetime.datetime.strptime(current_date, '%Y-%m-%d').date()
            next_date = curr_date + datetime.timedelta(days=1)
            current_date = next_date.strftime('%Y-%m-%d')

    else:
        for i in items:
            num = str(items[i]["commits"])

            sys.stdout.write(i)
            sys.stdout.write("  ")
            sys.stdout.write(num)
            sys.stdout.write((5 - len(num)) * " ")

            # Colour the weekend bars.
            if items[i]["weekend"]:
                sys.stdout.write("\033[94m")

            sys.stdout.write(block * int(items[i]["score"] * width))

            if items[i]["weekend"]:
                sys.stdout.write("\x1b[0m")

            sys.stdout.write("\n")

def filter(items, periodicity="day", author=""):
    """Filter entries by periodicity and author."""
    bars = OrderedDict()
    for i in items:
        # Extract the day/month/year part of the date.
        p = i["timestamp"][:10]
        is_weekend = False
        if periodicity == "week":
            p = datetime.datetime.strptime(p, "%Y-%m-%d").strftime("%Y/%V")
        elif periodicity == "month":
            p = i["timestamp"][:7]
        elif periodicity == "year":
            p = i["timestamp"][:4]
        else:
            is_weekend = (datetime.datetime.
                          strptime(p, "%Y-%m-%d").
                          weekday() > 4)
        # Filter by author.
        if author != "":
            if author not in i["author"]:
                continue

        if p not in bars:
            bars[p] = {"timestamp": i["timestamp"],
                       "commits": 0,
                       "weekend": is_weekend}
        bars[p]["commits"] += 1

    return bars


def get_scores(items):
    """Compute normalized scores (0-1) for commit numbers."""
    vals = [items[i]["commits"] for i in items]
    vals.append(0)

    xmin = min(vals)
    xmax = max(vals)

    # Normalize.
    out = OrderedDict()
    for i in items:
        out[i] = items[i].copy()
        out[i]["score"] = normalize(items[i]["commits"], xmin, xmax)

    return out


def get_log(after, before, reverse):
    """Return the list of git log from the git log command."""
    # 2018-01-01 00:00:00|author@author.com
    args = ["git", "log", '--pretty=format:%ai|%ae']

    if after:
        args.append("--after=%s" % (after,))
    if before:
        args.append("--before=%s" % (before,))

    items = []
    for o in check_output(args, universal_newlines=True, shell=False) \
            .split("\n"):
        c = o.split("|")
        items.append({"timestamp": c[0], "author": c[1]})

    if reverse:
        items.reverse()

    return items


def normalize(x, xmin, xmax):
    """Normalize a number to a 0-1 range given a min and max of its set."""
    return float(x - xmin) / float(xmax - xmin)


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

    p.add_argument("-c", "--colorize", action="store", dest="colorize",
                   type=bool, required=False, default=False,
                   help="colorize days")

    args = p.parse_args()

    """Invoke the utility."""
    items = []
    try:
        items = get_log(args.after, args.before, args.reverse)
    except Exception as e:
        print("error running 'git log': %s" % (e,))
        return

    filtered = filter(items, args.periodicity, args.author)
    scores = get_scores(filtered)
    if scores:
        print("%d commits over %d %s(s)" %
              (sum([filtered[f]["commits"] for f in filtered]),
               len(scores),
               args.periodicity))
        print_bars(scores, args.periodicity, args.colorize)
    else:
        print("No commits to plot")


if __name__ == "__main__":
    main()
