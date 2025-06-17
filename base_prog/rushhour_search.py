from collections import deque
from copy import deepcopy
import itertools
import heapq
import math 

def bfs(initial_state):
    visited = set()
    queue = deque([(initial_state, [])]) 

    while queue:
        state, path = queue.popleft()
        state_key = tuple((c.id, c.row, c.col) for c in state.cars.values())

        if state_key in visited:
            continue
        visited.add(state_key)

        if state.is_goal():
            return path

        for move in get_neighbors(state):
            next_state, move_info = move
            queue.append((next_state, path + [move_info]))

    return None 

def get_neighbors(state):
    neighbors = []
    for car in state.cars.values():
        if not car.movable:
            continue
        for delta in [-1, 1]:  
            new_state = deepcopy(state)
            car_copy = new_state.cars[car.id]
            if move_car(car_copy, delta, new_state):
                neighbors.append((new_state, (car.id, delta)))
    return neighbors

def move_car(car, delta, state):

    if car.orientation == 'h':
        new_col = car.col + delta
        new_tail = new_col + car.length - 1
        if 0 <= new_col <= state.grid_size - car.length:
    
            positions = state.occupied() - set(car.positions())
            for i in range(car.length):
                pos = (car.row, new_col + i)
                if pos in positions:
                    return False
            car.col = new_col
            return True

    elif car.orientation == 'v':
        new_row = car.row + delta
        new_tail = new_row + car.length - 1
        if 0 <= new_row <= state.grid_size - car.length:
            positions = state.occupied() - set(car.positions())
            for i in range(car.length):
                pos = (new_row + i, car.col)
                if pos in positions:
                    return False
            car.row = new_row
            return True
    return False

def a_star(start, is_goal, get_neighbors, heuristic, goal):
    counter = itertools.count()  
    heap = [(heuristic(start, goal), next(counter), start)] 
    came_from = {}
    cost = {start: 0}

    while heap:
        _, _, current = heapq.heappop(heap)

        if is_goal(current):
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path, cost

        for neighbor, move_cost in get_neighbors(current):
            new_cost = cost[current] + move_cost
            if neighbor not in cost or new_cost < cost[neighbor]:
                cost[neighbor] = new_cost
                came_from[neighbor] = current
                priority = new_cost + heuristic(neighbor, goal)
                heapq.heappush(heap, (priority, next(counter), neighbor))

    return [], cost

def heuristic_euclidean(positions:dict, node, goal):
    x1, y1 = positions[node]
    x2, y2 = positions[goal]
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def heuristic_manhattan(state, goal):
    car = state.cars['sh']
    return 5 - car.col 


def get_neighbors_astar(state):
    neighbors = []
    for car in state.cars.values():
        for delta in [-1, 1]:
            new_state = deepcopy(state)
            car_copy = new_state.cars[car.id]
            if move_car(car_copy, delta, new_state):
                new_state.move = (car.id, delta) 
                neighbors.append((new_state, 1))  
    return neighbors


def legal_head_positions(state, car):
    """
    Mengembalikan set posisi kepala mobil yang legal
    yaitu posisi yang tidak dihuni oleh mobil lain
    dan tidak keluar dari grid.
    """
    
    occupied_others = state.occupied() - set(car.positions())
    heads = set()

    if car.orientation == 'h':
  
        col = car.col
        while col-1 >= 0 and (car.row, col-1) not in occupied_others:
            col -= 1
            heads.add((car.row, col))
       
        col = car.col
        while col+car.length < state.grid_size \
              and (car.row, col+car.length) not in occupied_others:
            col += 1
            heads.add((car.row, col))
    else: 
        row = car.row
        while row-1 >= 0 and (row-1, car.col) not in occupied_others:
            row -= 1
            heads.add((row, car.col))
        row = car.row
        while row+car.length < state.grid_size \
              and (row+car.length, car.col) not in occupied_others:
            row += 1
            heads.add((row, car.col))

    heads.add((car.row, car.col))
    return heads


def ac3_filter(state):
    """
    Return: dict  car_id -> set(head_pos) sesudah arc‑consistency,
            atau None kalau ada domain kosong (dead‑end).
    """

    domains = {c.id: legal_head_positions(state, c) for c in state.cars.values()}
    queue   = deque((xi, xj)
                    for xi in domains for xj in domains if xi != xj)

    def cells_at(car, head_row, head_col):
        if car.orientation == 'h':
            return [(head_row, head_col + i) for i in range(car.length)]
        else:
            return [(head_row + i, head_col) for i in range(car.length)]

    def overlap(car_i_id, pos_i, car_j_id, pos_j):
        car_i = state.cars[car_i_id]
        car_j = state.cars[car_j_id]
        cells_i = cells_at(car_i, pos_i[0], pos_i[1])
        cells_j = cells_at(car_j, pos_j[0], pos_j[1])
        return any(c in cells_j for c in cells_i)


    while queue:
        xi, xj = queue.popleft()
        removed = set()
        for pos_i in domains[xi]:
        
            if all(overlap(xi, pos_i, xj, pos_j) for pos_j in domains[xj]):
                removed.add(pos_i)
        if removed:
            domains[xi] -= removed
            if not domains[xi]:
                return None                    
            for xk in domains:
                if xk != xi and xk != xj:
                    queue.append((xk, xi))
    return domains

def forward_check(domains, moved_id, moved_head, state):
    """
    Potong domain mobil lain berdasarkan posisi mobil yang baru digerakkan.
    Return False jika ada domain yang kosong → dead-end.
    """
    moved_car = state.cars[moved_id]

    def cells_at(car, r, c):
        return [(r, c+i) for i in range(car.length)] if car.orientation == 'h' \
               else [(r+i, c) for i in range(car.length)]

    occupied = set(cells_at(moved_car, *moved_head))

    for cid, dom in domains.items():
        if cid == moved_id:
            continue
        to_remove = {head for head in dom
                     if set(cells_at(state.cars[cid], *head)) & occupied}
        dom -= to_remove
        if not dom:
            return False 
    return True

def ac3_dfs(initial_state):
    """
    Depth‑First Search + satu kali AC‑3 + forward checking.
    Return path  [(car_id, delta), …]  atau  None kalau buntu.
    """
    domains = ac3_filter(initial_state)
    if domains is None:
        return None

    stack = [(initial_state, [], domains)]
    visited = set()

    while stack:
        state, path, doms = stack.pop()
        key = tuple((c.id, c.row, c.col) for c in state.cars.values())
        if key in visited:
            continue
        visited.add(key)

        if state.is_goal():
            return path

        for next_state, move_info in get_neighbors(state):
            cid, delta = move_info
            car = state.cars[cid]
            if car.orientation == 'h':
                new_head = (car.row, car.col + delta)
            else:
                new_head = (car.row + delta, car.col)

            new_domains = {k: set(v) for k, v in doms.items()}
            new_domains[cid] = {new_head}

            if not forward_check(new_domains, cid, new_head, next_state):
                continue 

            stack.append((next_state, path + [move_info], new_domains))

    return None

def iddfs(state, max_depth: int = 40):
    """
    Iterative Deepening DFS:
      –  optimise path length (sama dgn BFS)
      –  memori kecil
    """
    for depth_limit in range(max_depth + 1):

        visited_local = set()

        def dfs_ordered_neighbors(state):
            """
            Menghasilkan tetangga yang sudah di‑sort agar DFS cenderung
            menemukan solusi lebih cepat (lebih sedikit langkah).
            """
            neigh = get_neighbors(state)      
    
            def score(pair):
                st, (cid, delta) = pair
                if cid == 'sh':               
                    return 100 if delta == 1 else 50  
                red = st.cars['sh']
                return 5 - red.col             
    
            neigh.sort(key=score, reverse=True)
            return neigh
    
        def dfs_limited(st, path, depth):
      
            if st.is_goal():
                return path
      
            if depth == 0:
                return None
        
            key = tuple(sorted((c.id, c.row, c.col) for c in st.cars.values()))
            if key in visited_local:
                return None
            visited_local.add(key)

            for nxt_state, mv in dfs_ordered_neighbors(st):
                res = dfs_limited(nxt_state, path + [mv], depth - 1)
                if res:
                    return res

            visited_local.remove(key)       
            return None

        sol = dfs_limited(state, [], depth_limit)
        if sol:
            return sol    

    return None        


def ac3_iddfs(initial_state, max_depth: int = 40):
    """
    1. AC‑3 sekali di state awal – mendeteksi dead‑end cepat.
    2. Jika masih konsisten, jalankan IDDFS optimal.
    """
    if ac3_filter(initial_state) is None:
        return None                   
    return iddfs(initial_state, max_depth)


def ac3_bfs(initial_state):
    """
    • Jalankan AC‑3 sekali di root.  
    • Jika domain kosong ➜  None (dead‑end).  
    • Jika tidak, lanjut BFS normal – tetapi skip tetangga yang
      sudah terlihat (visited set).
    Return: list langkah [(car_id, delta), …] atau None.
    """

    if ac3_filter(initial_state) is None:
        return None                    


    visited = set()
    queue   = deque([(initial_state, [])]) 

    while queue:
        state, path = queue.popleft()
        key = tuple((c.id, c.row, c.col) for c in state.cars.values())
        if key in visited:
            continue
        visited.add(key)

        if state.is_goal():
            return path                 

        for next_state, move_info in get_neighbors(state):
            queue.append((next_state, path + [move_info]))

    return None 



import math
import random
from copy import deepcopy

def simulated_annealing_solver(initial_state, max_iter=5000, start_temp=500, cooling_rate=0.995, percobaan = 0):
    def is_goal(state):
        red_car = state.cars['sh']
        return red_car.col + red_car.length >= state.grid_size

    def cost(state):
        red_car = state.cars['sh']
        col = red_car.col + red_car.length
        blocking = 0
        for car in state.cars.values():
            if car.id == 'sh':
                continue
            if car.orientation == 'v':
                if car.col in range(col, state.grid_size) and red_car.row in [car.row + i for i in range(car.length)]:
                    blocking += 1
            elif car.orientation == 'h':
                if car.row == red_car.row and any(red_car.col < car.col + i < state.grid_size for i in range(car.length)):
                    blocking += 1
        return blocking + (5 - red_car.col)

    def get_neighbors_sa(state):
        neighbors = []
        for car in state.cars.values():
            for delta in [-1, 1]:
                new_state = deepcopy(state)
                car_copy = new_state.cars[car.id]
                if move_car(car_copy, delta, new_state):
                    neighbors.append((new_state, (car.id, delta)))
        return neighbors

    current = deepcopy(initial_state)
    current_cost = cost(current)
    temp = start_temp
    best = deepcopy(current)
    best_cost = current_cost
    path = []
    best_path = []

    for _ in range(max_iter):
        if is_goal(current):
            return path

        neighbors = get_neighbors_sa(current)
        if not neighbors:
            continue

        next_state, move_info = random.choice(neighbors)
        next_cost = cost(next_state)
        delta_e = current_cost - next_cost

        if delta_e > 0 or random.random() < math.exp(delta_e / temp):
            current = next_state
            current_cost = next_cost
            path.append(move_info)

            if current_cost < best_cost:
                best = deepcopy(current)
                best_cost = current_cost
                best_path = list(path)

        temp *= cooling_rate


    if best.is_goal():
        print("Best solution found.")
        return best_path
    else:
        # print(f"Si kocak udah ngulang sebanyak:{percobaan}")
        # simulated_annealing_solver(initial_state, max_iter=5000, start_temp=500, cooling_rate=0.995, percobaan=(percobaan+1))
        print("No solution found within max iterations.")
