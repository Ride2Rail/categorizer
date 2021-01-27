#!/usr/bin/env python3

from concurrent import futures
import logging

import sys
import json
import grpc
from lxml import etree
from collections import defaultdict

import numpy as np

from r2r import categorizer_pb2 as catpb
from r2r import categorizer_pb2_grpc as catpbgrcp


# set random seed
# ascii -> numbers
RANDOM_SEED = 830
np.random.seed(RANDOM_SEED)

# globals
NS = {None: "http://www.vdv.de/trias"}
CATEGORIES = ['Quick', 'Reliable', 'Cheap', 'Comfortable',
              'Door-to-door', 'Envirnmentally friendly', 'Short',
              'Multitasking', 'Social', 'Panoramic', 'Healthy']
THRESHOLDS = [0.390, 0.520, 0.580, 0.380,
              0.330, 0.410, 0.750, 0.380,
              0.320, 0.540, 0.630]

# errors
ERREMPTYTREE = 1
ERRINVALIDDATA = 2


class Categorizer(catpbgrcp.CategorizerServicer):

    def Categorize(self, request, context):

        data = request.offers
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')

        try:
            newtree = etree.fromstring(data.encode('utf-8'), parser=parser)
        except etree.XMLSyntaxError:
            print('Error: Empty tree.', file=sys.stderr)
            exit(ERREMPTYTREE)

        try:
            _trips = newtree.findall('.//Trip', namespaces=NS)
        except AttributeError:
            print('Error: Invalid TRIAS data, no trips found.', file=sys.stderr)
            exit(ERRINVALIDDATA)

        trips = {}
        for trip in _trips:
            trip_id = trip.find('.//TripId', namespaces=NS).text
            trips[trip_id] = trip

        cat_thresholds = dict((cat, th)
                              for cat, th in zip(CATEGORIES, THRESHOLDS)
                              )

        trip_feats = {}
        for trip_id, trip in trips.items():
            feats = np.random.normal(0.3, 0.2, 11)
            trip_feats[trip_id] = dict((cat, f)
                                       for cat, f in zip(CATEGORIES, feats))

        # import ipdb; ipdb.set_trace()

        trip_cats = defaultdict(dict)
        for cat in CATEGORIES:
            for trip_id in trip_feats:
                if trip_feats[trip_id][cat] >= cat_thresholds[cat]:
                    trip_cats[trip_id].update(
                        {cat: round(trip_feats[trip_id][cat], 3)}
                        )

        print(json.dumps(trip_cats), file=sys.stderr)

        categorization = {}
        for offer_id, categories in trip_cats.items():
            categorization[offer_id] = (catpb
                                        .CategorizationResponse
                                        .Categorization(categories=categories)
                                        )

        return catpb.CategorizationResponse(categorization=categorization)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    catpbgrcp.add_CategorizerServicer_to_server(Categorizer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    print('Launch Categorizer', file=sys.stderr)
    logging.basicConfig()
    serve()
