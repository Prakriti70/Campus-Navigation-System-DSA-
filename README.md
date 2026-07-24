# Pulchowk Smart Campus Navigation System

A desktop application that visualizes Data Structures & Algorithms concepts
using an interactive navigation system for Pulchowk Campus. Every core
data structure (linked list, queue, stack, binary min-heap) and graph
algorithm (BFS, DFS, Dijkstra) is implemented **manually** — no
`heapq`, `collections.deque`, `queue.Queue`, or graph libraries.

This project is not intended to compete with Google Maps. Its purpose is
to make abstract DSA concepts visible: you can watch a traversal happen
node by node, compare how BFS/DFS/Dijkstra disagree on "the best route,"
and see real execution-time measurements.

## Features

- Campus modeled as an **undirected weighted graph** (6 buildings —
  Canteen intentionally excluded)
- **Real aerial image of Pulchowk Campus** used as the exact map
  background (`assets/campus_map.png`) — never redrawn or simplified
- **Adjacency lists implemented as custom singly linked lists** — not
  Python lists or dicts of lists
- Manual **Queue** (FIFO, linked-list based) driving BFS
- Manual **Stack** (LIFO, linked-list based) driving iterative DFS
- Manual **binary min-heap** (array-based, hand-written sift-up/down)
  driving Dijkstra's priority queue
- **Layered canvas rendering**: aerial image → edges → nodes → animation
  state → labels → tooltip, all driven by one `zoom * world + pan`
  transform so everything stays perfectly aligned during zoom/pan
- **Mouse-wheel zoom, click-and-drag pan, double-click to reset view**
- Edge color states: gray (normal), yellow (current relaxation), green
  (visited traversal edge), dark blue (final shortest path)
- Node hover glow + tooltip showing direct connections; gentle pulse
  animation on the selected Start/End nodes
- Animated traversal: current node, visited nodes, and final path are
  color-coded and animated step by step using `Tkinter.after()` —
  the UI never freezes
- Pause / Resume animation, adjustable animation speed, and a
  step-by-step mode with a manual "Next Step" button
- Dark mode / Light mode toggle
- Legend explaining every node/edge color state
- Results panel: path, real walking distance, estimated walking time,
  and precise execution time
- Execution-time comparison chart (matplotlib) tracking the most recent
  run of each algorithm
- Export traversal + result to a `.txt` file
- Splash screen, About dialog, keyboard shortcuts (Ctrl+D theme,
  Ctrl+E export, Ctrl+Q quit, Enter to find path)
- Click a node on the map to set it as your destination

## Building-to-image mapping notes

The source image only had pins for 4 of the 6 graph vertices. Per
explicit project instructions:

- **Dean Office** is mapped to the "Institute of Engineering" pin (the
  small building directly behind Robotics Club) — there's no separate
  Dean Office pin in the source image.
- **Main Entry** is mapped to the midpoint between the ICTC Building pin
  and the "Pulchowk Campus ICT Tower" pin, representing the gate/lane
  between them — no distinct gate pin exists in the image.
- **Canteen** has been removed entirely and is not a graph node.

Edge weights are computed automatically from pixel distance between
building coordinates (see `SCALE_METERS_PER_PIXEL` in `config.py`) —
this scale factor is a placeholder calibrated to produce plausible
walking distances (15m–110m); replace it with a real measured distance
once you have one.

## Installation

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.9+. `tkinter` ships with standard Python installs on
Windows/macOS; on Linux install it separately if needed:
`sudo apt install python3-tk`.

Place your own campus aerial map image at `assets/campus_map.png` (any
size — it's resized automatically). Without it, the app falls back to a
plain grid background.

## Extending the campus

Every location and connection lives in **`config.py`** — nothing else
needs to change to add a building:

```python
CAMPUS_BUILDINGS["New Building"] = (x, y)
CAMPUS_EDGES.append(("New Building", "Library", 75))
```

## Project structure

```
pulchowk_nav/
├── main.py          # entry point + splash screen
├── gui.py           # Tkinter presentation layer only — no algorithm logic
├── graph.py          # Graph: vertices + adjacency (custom linked lists)
├── vertex.py          # Vertex data class
├── edge.py            # Edge data class
├── linked_list.py       # Manual singly linked list (used by adjacency lists, Queue, Stack)
├── ds_queue.py           # Manual FIFO queue (used by BFS)
├── ds_stack.py            # Manual LIFO stack (used by DFS)
├── min_heap.py             # Manual binary min-heap (used by Dijkstra)
├── algorithms.py            # BFS, DFS, Dijkstra — pure algorithm logic, no GUI
├── chart.py                  # matplotlib execution-time comparison chart
├── config.py                  # All coordinates, edges, colors, timing constants
├── assets/
│   ├── campus_map.png          # your campus image goes here
│   └── icons/
├── requirements.txt
└── README.md
```

**Why this split matters:** `graph.py`, `algorithms.py`, `linked_list.py`,
`ds_queue.py`, `ds_stack.py`, and `min_heap.py` have zero Tkinter
dependency. You can (and should, for your report) run and test all of the
actual DSA logic from a plain Python shell without ever opening the GUI.
`gui.py` only *consumes* these modules — it has no algorithm logic of
its own.

## Architecture notes

### Graph & adjacency lists
The graph is undirected and weighted. Each vertex's neighbors are stored
in a `LinkedList` of `Edge` objects — walking a vertex's neighbor list
means traversing linked nodes, exactly like a textbook adjacency list,
rather than indexing into a built-in Python container.

### Linked List
Singly linked, with a tracked tail pointer for O(1) `append`. Backs both
the adjacency lists and the Queue/Stack implementations, so one correct
implementation is reused everywhere instead of duplicating pointer logic.

### Queue (BFS)
FIFO: enqueue at the tail, dequeue from the head — both O(1) thanks to
the tracked tail pointer.

### Stack (DFS)
LIFO: push and pop both happen at the head — both O(1). DFS here is
**iterative** (uses the Stack directly) rather than recursive, avoiding
Python's recursion depth limit and making the traversal order easy to
animate step by step.

### Binary Min-Heap (Dijkstra)
Array-based binary heap with hand-written `_sift_up` / `_sift_down`.
Decrease-key is handled via **lazy deletion**: instead of searching the
heap for an existing entry, a new (smaller) entry is pushed for the same
vertex, and stale entries are simply skipped when popped if that vertex
is already finalized. This is the standard, simplest-to-verify-correct
approach for a heap without index tracking.

## Algorithm comparison

| Algorithm | Data structure | What it optimizes for | Guarantees shortest path? |
|---|---|---|---|
| BFS | Queue | Fewest edges (hops) | Only if all edges have equal weight |
| DFS | Stack | Neither — just explores deep-first | No |
| Dijkstra | Min-heap | Total edge weight (real distance) | Yes (non-negative weights) |

This is exactly why the app reports **both** BFS/DFS's real-world
distance and Dijkstra's — it's common (and worth noting in your report)
for BFS/DFS to return a route with *fewer buildings* that is actually
*longer in meters* than Dijkstra's answer.

## Time & space complexity

| Structure / Algorithm | Time | Space |
|---|---|---|
| Linked list append | O(1) | O(1) per node |
| Linked list search/remove | O(n) | — |
| Queue enqueue/dequeue | O(1) | O(n) |
| Stack push/pop | O(1) | O(n) |
| Min-heap push/pop | O(log n) | O(n) |
| BFS | O(V + E) | O(V) |
| DFS | O(V + E) | O(V) |
| Dijkstra (binary heap) | O((V + E) log V) | O(V) |

## Future improvements

- Persisting the execution-time chart's history across dark/light theme
  toggles (currently resets, since re-theming rebuilds the whole window)
- Multi-stop route planning (visit several buildings in one trip)
- A* search as a fourth algorithm option, using the existing min-heap
- Real-world distance calibration (replace the placeholder
  `SCALE_METERS_PER_PIXEL` with a measured ground-truth distance)
