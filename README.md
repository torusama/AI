# PACMAN AI PATHFINDING IN WEIGHTED GRID WORLD

## Introduction to Artificial Intelligence - Lab 1

### Group Members

| Name | Student ID |
|-----|-----|
| Võ Tấn An | 24127318 |
| Mai Khánh Băng | 24127147 |
| Nguyễn Ngọc Minh | 24127204 |
| Trần Minh Hiển | 24127037 |
| Đoàn Võ Ngọc Lâm | 24127435 |

# Project Description

This project simulates a **pathfinding problem in a weighted grid world similar to the Pac-Man game**.

Pacman acts as a delivery agent that must move from the **Start position (P)** to the **Goal (G)** while collecting all **Goods (T)** on the map.

The environment contains different terrain types that affect the movement cost.

The objective is to **find the optimal path with the minimum total cost**.

# Environment

The map is represented as a **2D grid**.

Each cell type has a specific meaning:

| Symbol | Meaning |
|------|------|
| P | Pacman (Start position) |
| G | Goal |
| W | Wall (cannot pass) |
| E | Empty cell |
| O | Obstacle / pothole |
| T | Goods |

# Movement Cost

| Cell Type | Cost |
|----------|------|
| E | 1 |
| O | 3 |
| W | Not allowed |

# State Representation

A state is defined as:

```
State = (x, y)
```

Where:

- `x` : row
- `y` : column

# Actions

Pacman can move in four directions:

- Up
- Down
- Left
- Right

Constraints:

- Cannot move outside the grid
- Cannot move into walls

# Search Algorithms Implemented

The project implements and compares the following algorithms:

Required algorithms:

- Breadth First Search (BFS)
- Depth First Search (DFS)
- Uniform Cost Search (UCS)
- A* Search

Additional algorithms:

- Greedy Best First Search
- Beam Search
- Bidirectional Search
- Iterative Deepening A* (IDA*)

# Heuristic Function

For heuristic-based algorithms, we use **Manhattan Distance**:

```
h(n) = |x_goal - x| + |y_goal - y|
```

This heuristic estimates the distance from the current node to the goal.

# GUI Features

The program provides a graphical interface that displays:

- Grid map
- Pacman position
- Goal position
- Walls and terrain types

During algorithm execution, the interface shows:

- Explored nodes
- Frontier nodes
- Final path found

Users can:

- Select the algorithm
- Select the map
- Run the simulation

# Output Information

After running an algorithm, the system displays:

- Algorithm used
- Path found
- Total path cost
- Path length
- Number of explored nodes
- Execution time

# Project Objective

The goal of this project is to **analyze and compare search algorithms** based on:

- Path cost
- Path length
- Number of explored nodes
- Execution time
- Optimality
- Memory usage (optional)

# References

Lab 1: Search Algorithms  
Introduction to Artificial Intelligence
