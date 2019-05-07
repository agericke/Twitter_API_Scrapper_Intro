import networkx as nx
from collections import Counter, defaultdict


def example_graph():
    """
    Create the example graph from class. Used for testing.
    Do not modify.
    """
    g = nx.Graph()
    g.add_edges_from([('A', 'B'), ('A', 'C'), ('B', 'C'), ('B', 'D'), ('D', 'E'), ('D', 'F'), ('D', 'G'), ('E', 'F'), ('G', 'F')])
    return g


def jaccard_wt(graph, node):
    """
    The weighted jaccard score, defined above.
    Args:
      graph....a networkx graph
      node.....a node to score potential new edges for.
    Returns:
      A list of ((node, ni), score) tuples, representing the 
                score assigned to edge (node, ni)
                (note the edge order)

    >>> jaccard_wt(example_graph(), 'G')
    [(('G', 'E'), 2.0416666666666665), (('G', 'B'), 0.9333333333333333), (('G', 'A'), 0.0), (('G', 'C'), 0.0)]
    """
    new_edges = defaultdict(float)
    # Obtain degrees of all nodes
    degrees = dict(nx.degree(graph))
    # Obtain neighbors of node parameter
    neighbors = set(graph.neighbors(node))
    # Compute first part of denominator
    denominator_a = 0
    for neigh in neighbors:
        denominator_a += degrees[neigh]
    # For every node, compute the jaccard similarity
    for n in graph.nodes():
        if (graph.has_edge(node, n) or node==n):
            continue
        numerator = 0
        denominator_b = 0
        # Obtain neighbors of the other node
        neighbors2 = set(graph.neighbors(n))
        # Obtain common neighbors
        common_neighbors = neighbors & neighbors2
        # Compute numerator
        for comm_n in common_neighbors:
            numerator += 1/degrees[comm_n]
        # Compute denominator_b
        for neigh2 in neighbors2:
            denominator_b += degrees[neigh2]            
        new_edges[tuple((node, n))] = numerator/(1/denominator_a + 1/denominator_b)
    return sorted(new_edges.items(), key=lambda x: (-x[1], x[0][1]))
    

def main():
    # Create graph
    g = example_graph()
    print(jaccard_wt(g, 'G'))


if __name__ == '__main__':
    main()
