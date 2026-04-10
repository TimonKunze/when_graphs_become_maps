// graph-tools.js

/* Gtools Module
 *
 * Requirements: math.js Module
 *
 */

const gtools = (function() {
  // Store public functions and variables
  const public = {};

  /*Create a matrix with specific value.*/
  public.createMatrix = function(m, n, fillVal) {
    let result = [];
    for(let i=0; i<n; i++) {
        result.push(new Array(m).fill(fillVal))
    }
    return result;
  }

  /* Randomly reverses the inner and outer lists in a two-
   * times nested list. Has no return value but modifies 
   * the list directly.
   */
  public.randomlyReverseLists = function (nestedList) {
    for (let i=0; i<nestedList.length; i++) {
      let randomBinary2 = Math.floor(Math.random()*2);
      if (randomBinary2) {
        nestedList[i][0].reverse();
      }

      let randomBinary3 = Math.floor(Math.random()*2);
      if (randomBinary3) {
        nestedList[i][1].reverse();
      }
      let randomBinary1 = Math.floor(Math.random()*2);
      if (randomBinary1) {
        nestedList[i].reverse();
      }
    }
  }

  /* Compare whether two arrays are equal */
  public.arraysEqual = function (a1,a2) {
    /* WARNING: arrays must not contain {objects} or behavior may be undefined */
    return JSON.stringify(a1)==JSON.stringify(a2);
  }

  // Sort paths by length and numbers {{{

  public.getListOfUniqueEntries = function (lst) {
    let lstUnique = [];
    for (let entry of lst) {
      let isUnique = true;
      for (let uniqueEntry of lstUnique) {
        if (public.arraysEqual(entry, uniqueEntry)) {
          isUnique = false;
          break;
        }
      }
      if (isUnique) {
        lstUnique.push(entry);
      }
    }
    return lstUnique;
  }

  public.sortPathPairsByLen = function(pathPairs) {
    return pathPairs.map(pair => pair.sort((a, b) => a.length - b.length));
  }

  public.sortPathPairsByNb = function (pathPairs) {
      let pathPairsNbSort = [];
      for (pathPair of pathPairs) {
        pathPairRev = [];
        for (path of pathPair) {
          if (path[0] > path[path.length-1]) {
            pathPairRev.push(path.reverse());
          } else {
            pathPairRev.push(path);
          }
        pathPairsNbSort.push(pathPairRev);
        }
      }
      return pathPairsNbSort;
  }

  public.sortPathPairs = function (pathPairs) {
    let pathPairsLenSort = public.sortPathPairsByLen(pathPairs);
    pathPairsSort = public.sortPathPairsByNb(pathPairsLenSort);
    return pathPairsSort;
  }


  // }}}

  // Test Graph conntectedness {{{

  public.transformToAdjacencyObject = function(nbNodes, adjList) {
      const adjacencyObject = {};
      for (let i = 0; i < nbNodes; i++) {
          adjacencyObject[i] = [];
      }
      for (const [node1, node2] of adjList) {
        adjacencyObject[node1].push(node2);
        adjacencyObject[node2].push(node1);
      }
      return adjacencyObject;
  }

  public.isConnected = function(graph) {
    const visited = new Set(); // Track visited nodes
    const nodes = Object.keys(graph); // Get all nodes from the graph
    if (nodes.length === 0) return true; // Empty graph is considered connected
    const startNode = parseInt(nodes[0]);

    // Depth-First Search (DFS) function
    function dfs(node) {
      if (!visited.has(node)) {
        visited.add(node); // Mark node as visited
        for (const neighbor of graph[node]) {
          dfs(neighbor); // Visit all neighbors
        }
      }
    }
    // Start DFS from the first node
    dfs(startNode);
    return visited.size === nodes.length; 
  }


  // }}}

  return public;
})();



