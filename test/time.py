from timeit import timeit

setup = """
from vou.person import Person
from vou.simulation import Simulation
from vou.visualize import visualize
from random import Random, randint
"""

stmt = """
seed = randint(1, 1e10)
person = Person(rng=Random(seed))

simulation = Simulation(person=person, rng=Random(seed))
simulation.simulate()

fig = visualize(person)
"""

N = 20

time = timeit(stmt, setup, number=N) / N

print(f"Average time per run: {time}")
