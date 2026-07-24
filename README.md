# Pulchowk Smart Campus Navigation System

A Python desktop app that visualizes graph traversal and shortest-path algorithms on a campus map.

## What this project does

This project models Pulchowk Campus as a weighted graph and demonstrates how different algorithms behave when finding routes between buildings:

- BFS
- DFS
- Dijkstra's algorithm

The UI shows the map, animated traversal, path results, and execution-time comparison charts.

## Features

- Interactive campus map interface
- Animated graph exploration
- Manual linked-list, queue, stack, and min-heap implementations
- Route comparison across BFS, DFS, and Dijkstra
- Dark/light theme support
- Export of results and traversal output

## Tech stack

- Python
- Tkinter
- Matplotlib
- Pillow

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

## Project structure

```text
pulchowk_nav/
├── main.py
├── gui.py
├── algorithms.py
├── graph.py
├── linked_list.py
├── ds_queue.py
├── ds_stack.py
├── min_heap.py
├── config.py
├── assets/
└── requirements.txt
```

## Notes

This project focuses on understanding data structures and algorithms through visualization rather than on real-world navigation accuracy.

