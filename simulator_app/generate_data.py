import sys
import json
import numpy as np
import networkx as nx
import pandas as pd
import os

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

def generate_graph():
    '''
    Generates a graph based on the nodes/edges files provided below.
    '''
    nodes_df = pd.read_csv(os.path.join(THIS_DIR,'mps.csv'), index_col=0)
    edges_df = pd.read_csv(os.path.join(THIS_DIR,'mps_edges.csv'), index_col=0)

    node_names = [{"name":'n%s' % x, "infected":False} for x in nodes_df.new_id]
    links = []
    for i, row in edges_df.iterrows():
        d = {
            'source': 'n%s' % row['p1'],
            'target': 'n%s' % row['p2'],
        }
        links.append(d)
    return node_names, links, None


def generate_graph_sf(N):
    '''
    Generates a scale-free network.  See networkx documentation on
    the parameters, etc.
    '''
    alpha = 0.01
    beta = 0.5
    gamma = 0.49
    G = nx.scale_free_graph(N, alpha=alpha, beta=beta, gamma=gamma)
    j = nx.node_link_data(G)
    nodes = j['nodes']
    links = j['links']
    
    node_names = [{"name":'n%s' % x['id'], "infected":False} for x in nodes]
    final_links = []
    seen_links = set()
    for link in links:
        if link['source'] != link['target']: # ignore self-links
            pairing = (link['source'], link['target'])
            if not pairing in seen_links:
                d = {
                    'source': 'n%s' % link['source'],
                    'target': 'n%s' % link['target'],
                }
                final_links.append(d)
                seen_links.add(pairing)
                seen_links.add(pairing[::-1])
    return node_names, final_links, None


def generate_graph_normal(N):
    '''
    Given integer N, generate a graph for that many nodes
    Each connection has q links where q is sampled
    from a normal distribution
    '''
    adj = np.zeros((N,N), dtype=np.int)
    for i in range(N):
        pos = False
        while not pos:
            nn = int(np.random.normal(5,15))
            if nn > 0:
                pos = True
        existing_neighbors = np.sum(adj[i,:i])
        additional_needed = nn - existing_neighbors
        if additional_needed > 0:
            available_idx = np.arange(i+1,N)
            np.random.shuffle(available_idx)
            try:
                if additional_needed > len(available_idx):
                    additional_needed = len(available_idx)
                chosen_idx = available_idx[:additional_needed]
            except IndexError as ex:
                print(ex)
                print('N: %d' % N)
                print('nn: %d' % nn)
                print('exist: %d' % existing_neighbors)
                print('needed: %d' % additional_needed)
                print(available_idx)

            adj[i, chosen_idx] = 1
            adj[chosen_idx, i] = 1

    # have an adj matrix
    node_names = [{"name":'n%d' % i, "infected":False} for i in range(N)]

    neighbors = []
    for i in range(N):
        source = "n%d" % i
        for j in range(i+1,N):
            if adj[i,j] == 1:
                target = "n%d" % j
                d = {'source':source, 'target': target}
                neighbors.append(d)
    return (node_names, neighbors, adj)

