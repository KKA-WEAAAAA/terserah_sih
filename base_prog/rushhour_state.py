import csv

class Car:
    def __init__(self, cid, orientation, length, row, col):
        self.id = cid
        self.orientation = orientation   
        self.length = length
        self.row = row
        self.col = col
        self.movable = orientation in ('h', 'v', 'sh') 
    def positions(self):
        """Return list of coordinates occupied by the car."""
        return [
            (self.row + i if self.orientation == 'v' else self.row,
             self.col + i if self.orientation == 'h' else self.col)
            for i in range(self.length)
        ]

class RushHourState:
    def __init__(self, cars, grid_size=6):
        self.cars = cars 
        self.grid_size = grid_size

    @staticmethod
    def from_csv(path):
        cars = {}
        id_counter = {'h': 0, 'v': 0, 'b': 0}
        with open(path) as f:
            reader = csv.reader(f)
            for row in reader:
                ori, length, r, c = row[0], int(row[1]), int(row[2]), int(row[3])
                if ori == 'sh':
                    id = 'sh'
                    ori = 'h'
                else:
                    id_counter[ori] += 1
                    id = ori + str(id_counter[ori])
                cars[id] = Car(id, ori, length, r, c)
        return RushHourState(cars)

    def is_goal(self):
        """Goal: special car 'sh' reaches right edge"""
        sh = self.cars['sh']
        return sh.col + sh.length == self.grid_size

    def occupied(self):
        """Return set of all occupied positions"""
        occ = set()
        for car in self.cars.values():
            occ.update(car.positions())
        return occ
    def __eq__(self, other):
        if not isinstance(other, RushHourState):
            return False
        return all(
            (self.cars[c.id].row, self.cars[c.id].col) ==
            (other.cars[c.id].row, other.cars[c.id].col)
            for c in self.cars.values()
        )

    def __hash__(self):
        return hash(tuple((c.id, c.row, c.col) for c in self.cars.values()))
