import pandas as pd
import networkx as nx

import src.graph_utils as sgu

from src.config import path


def get_G(adj_m):
    G = nx.from_numpy_array(adj_m)
    return G


def build_graph_lex(save=False):
    """
    Build lexicon of all used graphs and some of their properties...
    """
    # Initialize
    graph_lex = pd.DataFrame([
        {'hex': '3870C0',
         'notes': "first used graph",
         "date": "2023-10-10",
         "experiments": ["pilot_1", "pilot_2", "pilot_3", "pilot_4", "pilot_5"]
         },
        {'hex': '102484B0',
         'notes': "new found graph, without loops",
         "date": "2024-08-27",
         'experiments': [],
         },
        {'hex': '10248905',
         'notes': "new found graph, without loops",
         "date": "2024-08-27",
         "experiments": ["batch_1"],
         "pos_batch1": [[220, 550], [220, 770], [440, 110], [440, 220], [550, 440], [660, 220], [770, 220], [770, 330]],
         "grid_pos_batch1": 110,
         "eCongrPairs": [[[5, 6, 7], [1, 7, 6, 5]], [[5, 6, 7], [1, 7, 6, 2]], [[1, 7, 6, 5], [0, 7, 1]], [[2, 6, 5, 3], [1, 7, 6, 5, 3]], [[1, 7, 6, 2], [0, 7, 1]], [[2, 6, 5], [1, 7, 6, 5]], [[4, 1, 7], [1, 7, 6, 5]], [[2, 6, 5], [1, 7, 6, 2]], [[4, 1, 7], [1, 7, 6, 2]], [[5, 6, 7], [0, 7, 6, 5]], [[3, 5, 6], [1, 7, 6, 5]], [[3, 5, 6], [1, 7, 6, 2]], [[5, 6, 7], [0, 7, 6, 2]], [[0, 7, 6, 5], [0, 7, 1]], [[2, 6, 7], [1, 7, 6, 5]], [[2, 6, 5], [0, 7, 6, 5]], [[4, 1, 7], [0, 7, 6, 5]], [[2, 6, 7], [1, 7, 6, 2]]],
         "eIncongrPairs": [[[3, 5, 6], [4, 1, 7, 6]], [[2, 6, 5, 3], [5, 6, 7]], [[2, 6, 7], [3, 5, 6, 7]], [[0, 7, 1, 4], [2, 6, 7]], [[4, 1, 7, 6, 5], [4, 1, 7, 6]], [[1, 7, 6, 5], [1, 7, 6]], [[1, 7, 6, 2], [1, 7, 6]], [[2, 6, 7], [4, 1, 7, 6]], [[0, 7, 6, 5], [0, 7, 6]], [[0, 7, 6, 2], [0, 7, 6, 5, 3]], [[3, 5, 6, 7], [4, 1, 7, 6, 5]], [[2, 6, 7, 1, 4], [3, 5, 6, 7, 1, 4]], [[0, 7, 1, 4], [4, 1, 7, 6, 5]], [[1, 7, 6, 2], [1, 7, 6, 5, 3]], [[0, 7, 1], [2, 6, 5, 3]], [[1, 7, 6, 5, 3], [1, 7, 6, 5]], [[2, 6, 5, 3], [4, 1, 7]], [[2, 6, 5, 3], [2, 6, 5]]],
         "wCongrPairs": [[[5, 6, 7], [0, 7, 1, 4]], [[3, 5, 6], [0, 7, 1, 4]], [[2, 6, 5], [0, 7, 1, 4]], [[2, 6, 7], [0, 7, 1, 4]], [[3, 5, 6, 7], [2, 6, 7, 1, 4]], [[0, 7, 6], [0, 7, 1, 4]], [[5, 6, 7], [4, 1, 7, 6]], [[2, 6, 7, 1, 4], [2, 6, 5, 3]], [[4, 1, 7, 6], [3, 5, 6]], [[3, 5, 6, 7], [4, 1, 7, 6, 5]], [[1, 7, 6], [0, 7, 1, 4]], [[5, 6, 7], [1, 7, 6, 2]], [[3, 5, 6], [1, 7, 6, 2]], [[5, 6, 7], [0, 7, 6, 2]], [[4, 1, 7, 6], [2, 6, 5]], [[2, 6, 7], [4, 1, 7, 6]], [[0, 7, 6, 5], [2, 6, 7, 1, 4]], [[3, 5, 6], [0, 7, 6, 2]]],
         "wIncongrPairs": [[[0, 7, 6, 5], [1, 7, 6]], [[1, 7, 6, 2], [4, 1, 7]], [[0, 7, 1], [4, 1, 7, 6]], [[1, 7, 6, 2], [1, 7, 6, 5, 3]], [[2, 6, 7, 1, 4], [3, 5, 6, 7, 1, 4]], [[2, 6, 7], [3, 5, 6, 7]], [[2, 6, 5], [3, 5, 6, 7]], [[0, 7, 6, 2], [0, 7, 6, 5, 3]], [[0, 7, 6], [2, 6, 5, 3]], [[0, 7, 6, 2], [4, 1, 7]], [[0, 7, 6, 5, 3], [1, 7, 6, 2]], [[0, 7, 1, 4], [2, 6, 7, 1, 4]], [[0, 7, 1], [1, 7, 6, 2]], [[1, 7, 6], [2, 6, 5, 3]], [[1, 7, 6, 5, 3], [4, 1, 7, 6]], [[0, 7, 1], [0, 7, 6, 2]], [[1, 7, 6, 5], [4, 1, 7]], [[0, 7, 6, 5, 3], [4, 1, 7, 6]]],
         },
        {'hex': '9DF8',
         'notes': "K3,3 graph",
         "date": "2025-12-27",
         "experiments": [],
         },
        {'hex': '13871C0000',
         'notes': "K3,3 graph with an additional 3 unconnected nodes",
         "date": "2025-12-27",
         "experiments": [],
         },
    ])

    # Add automatically
    graph_lex["date"] = graph_lex["date"].apply(pd.to_datetime)
    graph_lex["adj_m"] = graph_lex["hex"].apply(sgu.base16_to_adjm)
    graph_lex["strict_upper_tri"] = graph_lex["adj_m"].apply(sgu.get_upper_triangle_without_diagonal)
    graph_lex["nb_nodes"] = graph_lex["adj_m"].apply(len)
    graph_lex["nb_edges"] = graph_lex["strict_upper_tri"].apply(sum)
    graph_lex["len_cyc_bases"] = graph_lex["adj_m"].apply(get_G).apply(sgu.get_cycle_lengths)
    graph_lex["spars"] = graph_lex.apply(lambda row: sgu.calculate_sparsity(row["nb_nodes"], row["nb_edges"]), axis=1)
    graph_lex["undirect"] = graph_lex["adj_m"].apply(get_G).apply(lambda G: not G.is_directed())
    graph_lex["connect"] = graph_lex["adj_m"].apply(get_G).apply(nx.is_connected) # or nx.is_strongly_connected...
    graph_lex["nb_hubs"] = graph_lex["adj_m"].apply(get_G).apply(lambda G: sgu.count_hubs(G, threshold=2))

    if save:
        fp = path["data"] / "graph_lex.csv"
        graph_lex.to_csv(fp, index=False) 

    return graph_lex


if __name__ == '__main__':

    graph_lex = build_graph_lex(save=True)
    print(graph_lex)

    print(graph_lex.loc[2]["adj_m"])
