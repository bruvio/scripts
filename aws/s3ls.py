#!/usr/bin/env python3
"""
A script for listing all the objects in an S3 prefix.

Objects are printed to stdout as JSON, one object per line.
"""

import argparse
import datetime
import json
import sys

import tqdm

from _common import create_s3_session, parse_s3_uri


def parse_args():
    parser = argparse.ArgumentParser(
        prog="s3ls", description="List all the objects in an S3 prefix"
    )

    parser.add_argument("S3_URI")
    parser.add_argument(
        "--with-versions",
        action="store_true",
        help="List every version of the objects in S3, not just the latest version",
    )
    parser.add_argument(
        "--start-after", help="Start listing objects at the given key", default=""
    )

    return parser.parse_args()


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()


def get_objects(sess, **kwargs):
    """
    Generates every object in an S3 bucket.
    """
    paginator = sess.client("s3").get_paginator("list_objects_v2")

    for page in paginator.paginate(**kwargs):
        yield from page["Contents"]


def get_object_versions(sess, **kwargs):
    """
    Generates every version of an object in an S3 bucket.
    """
    s3_client = sess.client("s3")
    paginator = s3_client.get_paginator("list_object_versions")

    for page in paginator.paginate(**kwargs):
        for key in ("Versions", "DeleteMarkers"):
            try:
                yield from page[key]
            except KeyError:
                pass


if __name__ == "__main__":
    args = parse_args()

    s3_list_args = parse_s3_uri(args.S3_URI)

    sess = create_s3_session(args.S3_URI)

    if "--with-versions" in sys.argv:
        iterator = get_object_versions
        s3_list_args["KeyMarker"] = args.start_after
    else:
        iterator = get_objects
        s3_list_args["StartAfter"] = args.start_after

    for s3_obj in tqdm.tqdm(iterator(sess, **s3_list_args)):
        print(json.dumps(s3_obj, cls=DatetimeEncoder))
