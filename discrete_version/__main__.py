import random

from vou.person import Person
from vou.opioid import Opioid
from vou.visualize import visualize_opioid_use
from vou.timer import Timer

seed = 98544
rng = random.Random(seed)

# Instantiate person
person = Person(rng=rng, opioid=Opioid(rng=rng))

# Instantiate timer
timer = Timer(person=person, rng=rng, run_days=78 * 365,)

# Run simulation
timer.simulate()

# View results
person.risk_multiplier
visualize_opioid_use(person, seed)
