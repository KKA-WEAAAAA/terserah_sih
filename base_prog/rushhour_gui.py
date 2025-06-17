import os, threading, time, pygame, sys
from rushhour_state import RushHourState
from rushhour_search import *

CELL_SIZE = 80
HEADER_HEIGHT = 60 
SCREEN_SIZE = CELL_SIZE * 6
WINDOW_HEIGHT = SCREEN_SIZE + HEADER_HEIGHT

COLORS = {
    'sh': (255, 0, 0),
    'h': (0, 255, 0),
    'v': (0, 0, 255),
    'b': (80, 80, 80)
}

# parameter untuk simulated annealing
MAX_ITER = 2000
START_TEMP = 100
COOLING_RATE = 0.995


pygame.init()
screen = pygame.display.set_mode((SCREEN_SIZE, WINDOW_HEIGHT))
pygame.display.set_caption("Rush Hour")
font = pygame.font.SysFont(None, 36)

car_images = {
    'sh2': pygame.image.load('aset\\tcar-h.png'),
    'h2': pygame.image.load('aset\\car-h.png'),
    'h3': pygame.image.load('aset\\truck-h.png'),
    'v2': pygame.image.load('aset\\car-v.png'),
    'v3': pygame.image.load('aset\\truck-v.png'),
    'b1': pygame.image.load('aset\\box.png')
}

def draw_background_grid():
    screen.fill((42, 42, 41))

    for i in range(7):
        
        pygame.draw.line(screen, (21, 21, 20),
                         (0, i * CELL_SIZE + HEADER_HEIGHT),
                         (SCREEN_SIZE, i * CELL_SIZE + HEADER_HEIGHT), 2)
  
        pygame.draw.line(screen, (21, 21, 20),
                         (i * CELL_SIZE, HEADER_HEIGHT),
                         (i * CELL_SIZE, HEADER_HEIGHT + SCREEN_SIZE), 2)


def draw_state(state, info_text=None):
    draw_background_grid()
    for car in state.cars.values():
        x = car.col * CELL_SIZE
        y = car.row * CELL_SIZE + HEADER_HEIGHT

        key = ''

        if car.id == 'sh':
            key = 'sh2'
        elif car.id == 'b':
            key = 'b1'
        else:
            key = f'{car.orientation}{car.length}'

        image = car_images.get(key)

        if image:
            screen.blit(image, (x, y))
        else:
            w = CELL_SIZE * (car.length if car.orientation == 'h' else 1)
            h = CELL_SIZE * (car.length if car.orientation == 'v' else 1)
            pygame.draw.rect(screen, (200, 0, 200), pygame.Rect(x, y, w, h), border_radius=8)
    
    if info_text:
        text_surface = font.render(info_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_SIZE // 2, HEADER_HEIGHT // 2))
        screen.blit(text_surface, text_rect)
    pygame.display.flip()


def draw_menu():
    screen.fill((255, 255, 255))
    title = font.render("Pilih Algoritma:", True, (0, 0, 0))
    bfs_text = font.render("1. BFS", True, (0, 0, 0))
    astar_text = font.render("2. A* (Manhattan)", True, (0, 0, 0))
    ac3_text   = font.render("3. AC-3 + BFS",     True, (0, 0, 0))
    sa_text   = font.render("4. Simulated Annealing",     True, (0, 0, 0))

 
    title_pos = (50, 100)
    bfs_pos = (50, 150)
    astar_pos = (50, 200)
    ac3_pos   = (50, 250) 
    sa_pos   = (50, 300) 

    bfs_rect = bfs_text.get_rect(topleft=bfs_pos)
    astar_rect = astar_text.get_rect(topleft=astar_pos)
    ac3_rect   = ac3_text.get_rect(topleft=ac3_pos)
    sa_rect   = sa_text.get_rect(topleft=sa_pos)


    screen.blit(title, title_pos)
    screen.blit(bfs_text, bfs_pos)
    screen.blit(astar_text, astar_pos)
    screen.blit(ac3_text, ac3_pos)  
    screen.blit(sa_text, sa_pos)  
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 'bfs'
                elif event.key == pygame.K_2:
                    return 'astar'
                elif event.key == pygame.K_3:                      
                    return 'ac3'
                elif event.key == pygame.K_4:                      
                    return 'sa'

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # klik kiri
                mouse_pos = event.pos
                if bfs_rect.collidepoint(mouse_pos):
                    return 'bfs'
                elif astar_rect.collidepoint(mouse_pos):
                    return 'astar'
                elif ac3_rect.collidepoint(mouse_pos):
                    return 'ac3'
                elif sa_rect.collidepoint(mouse_pos):
                    return 'sa'

def keep_gui_alive():
    """Pump event & redraw splash saat solver bekerja di thread lain."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    loading = font.render("Solving...", True, (0,0,0))
    screen.blit(loading, (300, 20))
    pygame.display.flip()

def draw_dataset_menu(dataset_files):
    screen.fill((255, 255, 255))
    title = font.render("Pilih Dataset:", True, (0, 0, 0))
    screen.blit(title, (50, 50))

    item_rects = []
    for idx, fname in enumerate(dataset_files):
        text = font.render(f"{idx+1}. {fname}", True, (0, 0, 0))
        pos = (50, 100 + idx * 30)
        screen.blit(text, pos)
        rect = pygame.Rect(pos[0], pos[1], text.get_width(), text.get_height())
        item_rects.append((rect, idx))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for rect, idx in item_rects:
                    if rect.collidepoint(mouse_pos):
                        return idx



def main():


    dataset_folder = r'dataaset'
    dataset_files  = [f for f in os.listdir(dataset_folder) if f.endswith('.csv')]

    sel = draw_dataset_menu(dataset_files)
    csv_path = os.path.join(dataset_folder, dataset_files[sel])

    state    = RushHourState.from_csv(csv_path)

    algo = draw_menu()          

    solution = []
    solving = True
    start_time = time.time()

    def run_solver():
        nonlocal solution, solving
        if algo == 'bfs':
            solution = bfs(state)
        elif algo == 'astar':
            goal_pos = (state.cars['sh'].row, 5)
            sol_states, _ = a_star(
                state,
                lambda s: s.is_goal(),
                get_neighbors_astar,
                heuristic_manhattan,
                goal_pos
            )
            solution = [
                (s.move[0], s.move[1])
                for s in sol_states[1:] if hasattr(s, 'move')
            ]
        elif algo == 'ac3':
            solution = ac3_bfs(state, )
        elif algo == 'sa':
            solution = simulated_annealing_solver(state, max_iter=MAX_ITER, start_temp=START_TEMP, cooling_rate=COOLING_RATE)
        solving = False

    threading.Thread(target=run_solver, daemon=True).start()

  
    while solving:
        keep_gui_alive()
        time.sleep(0.05)

    elapsed_time = time.time() - start_time
    step_count = len(solution) if solution else 0

    info_string = f"{algo.upper()} | Langkah: {step_count} | Waktu: {elapsed_time:.2f}s"
    draw_state(state, info_string)
    print(f"Algoritma: {algo.upper()} | Langkah = {step_count} | Waktu = {elapsed_time:.2f} detik")

    pygame.display.flip()

    print("Tekan SPACE untuk mulai animasi.")


    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False

    clock = pygame.time.Clock()
    step = 0
    running = True
    while running:
        clock.tick(40)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if solution and step < len(solution):
            car_id, delta = solution[step]
            move_car(state.cars[car_id], delta, state)
            draw_state(state, info_string)
            pygame.display.flip()
            step += 1

        elif step >= len(solution):
            for event in pygame.event.get():
                if event.type in [pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN]:
                    running = False

    pygame.quit()

if __name__ == '__main__':
    main()
