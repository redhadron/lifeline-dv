
import math
from enum import Enum
import operator
import numbers


KSP_LFOX_RATIO_PARTS = (9,11)
KSP_LFOX_COEFFICIENTS = tuple(item/sum(KSP_LFOX_RATIO_PARTS) for item in KSP_LFOX_RATIO_PARTS) 
STANDARD_GRAVITY = 9.80665

ERROR_TOLERANCE_METERS = 1.0
ERROR_TOLERANCE_TONS = 0.1

# helper methods -----------------------------

def operate_on_dictionary_vector_in_place(a, b, *, operator_fun, lock_axes=True, default_value=None):
  for key, value in b.items():
    if key not in a:
      if lock_axes:
        raise KeyError(f"axes are locked but {key} is a key not in dict a.")
      else:
        a[key] = default_value
    a[key] = operator_fun(a[key], value)

def add_dictionary_vector_in_place(a, b, **kwargs):
  return operate_on_dictionary_vector_in_place(a, b, operator_fun=operator.add, **kwargs)
  
def subtract_dictionary_vector_in_place(a, b, **kwargs):
  return operate_on_dictionary_vector_in_place(a, b, operator_fun=operator.sub, **kwargs)
_dictVect = {5:10, 15:20}
subtract_dictionary_vector_in_place(_dictVect, {5:1, 15:2})
assert _dictVect == {5:9, 15:18}
del _dictVect

def scaled_dictionary_vector(input_dict, scale):
  return {key:(value*scale) for key, value in input_dict.items()}
assert scaled_dictionary_vector({1:2, 3:4}, 10) == {1:20, 3:40}

def assert_equal(a, b):
  if a != b:
    raise AssertionError(f"{a} does not equal {b}.")

# end of helper methods -------------------------


def tsiolkovsky(Isp, m0, mf) -> float:
  assert 0 < Isp
  assert 0 < mf < m0
  return Isp*STANDARD_GRAVITY*math.log(m0/mf)
assert abs(tsiolkovsky(300, 2.0, 1.0) - 2039) < ERROR_TOLERANCE_METERS

class Resource(Enum):
  LIQUID_FUEL = "LIQUID_FUEL"
  OXIDIZER = "OXIDIZER"
  ORE = "ORE"
  MONOPROPELLANT = "MONOPROPELLANT"
  XENON_GAS = "XENON_GAS"
LF = Resource.LIQUID_FUEL
OX = Resource.OXIDIZER
ORE = Resource.ORE

RESOURCE_KILOGRAMS_PER_UNIT = {
  Resource.LIQUID_FUEL: 5,
  Resource.OXIDIZER: 5,
  Resource.MONOPROPELLANT: 4,
  Resource.XENON_GAS: 0.1,
  Resource.ORE: 20,
} # https://wiki.kerbalspaceprogram.com/wiki/Resource
  

class Engine:

  def __init__(self, *, Isp, thrust_kn, resource_flow_rates=None):
    self._Isp, self._thrust_kn = (Isp, thrust_kn)
    assert isinstance(resource_flow_rates, dict)
    self._resource_flow_rates = resource_flow_rates
    
  def get_Isp(self):
    return self._Isp
    
  def get_thrust_kn(self):
    return self._thrust_kn
    
  def get_resource_flow_rates(self):
    return self._resource_flow_rates
    
  def get_mass_flow_rate(self):
    return sum(self.get_resource_flow_rates().values())
    


STOCK_ENGINES = {
  "Terrier": Engine(Isp=345, thrust_kn=60, resource_flow_rates={LF: 1.596, OX: 1.951}),
  "Nerv": Engine(Isp=800, thrust_kn=60, resource_flow_rates={LF: 1.53}),
}

class EngineCluster(Engine):
  def __init__(self, template_engine, *, count, thrust_limiter):
    # thrust limiter is a multiplier, not a percentage.
    assert isinstance(template_engine, Engine)
    assert isinstance(count, int)
    assert count >= 1
    assert thrust_limiter >= 0
    self.template_engine, self.count, self.thrust_limiter = (template_engine, count, thrust_limiter)
  
  def _get_total_performance_multiplier(self):
    return self.count * self.thrust_limiter
  
  def get_Isp(self):
    return self.template_engine.get_Isp()
  
  def get_thrust_kn(self):
    return self.template_engine.get_thrust_kn() * self._get_total_performance_multiplier()
    
  def get_resource_flow_rates(self):
    return scaled_dictionary_vector(self.template_engine.get_resource_flow_rates(), self._get_total_performance_multiplier())
  
  # get_mass_flow_rate is inherited from Engine.

_ec = EngineCluster(STOCK_ENGINES["Nerv"], count=2, thrust_limiter=1.0)
assert _ec.get_thrust_kn() == 120
assert _ec.get_mass_flow_rate() == 2 * STOCK_ENGINES["Nerv"].get_mass_flow_rate()
del _ec


class EngineBlock(Engine):
  def __init__(self, engines):
    assert isinstance(engines, list)
    self.engines = engines
    self.thrust_multiplier = 1.0
  
  def get_Isp(self):
    raise NotImplementedError()
    # impl gen_track_previous, get_shared_value
    
  def get_thrust_kn(self):
    return sum(engine.get_thrust_kn() for engine in self.engines)
    
  def get_resource_flow_rates(self):
    result = dict()
    for engine in self.engines:
      add_dictionary_vector_in_place(result, engine.get_resource_flow_rates(), lock_axes=False, default_value=0)
    return result
    

class Ship:

  def __init__(self, *,
      speed=0.0,
      resource_tons: None | dict[Resource, numbers.Real] = None,
      resource_units: None | dict[Resource, int] = None,
      dry_mass=None,
      total_mass=None):
    
    # calculate resource tons if necessary:
    if resource_tons is None:
      if resource_units is None:
        raise ValueError("either resource_tons or resource_units must be provided.")
      else:
        assert isinstance(resource_units, dict)
        resource_tons = {key:val*RESOURCE_KILOGRAMS_PER_UNIT[key]/1000 for key, val in resource_units.items()}
    assert isinstance(resource_tons, dict)
    
    # calculate dry mass if necessary:
    if dry_mass is None:
      if total_mass is None:
        raise ValueError("either dry_mass or total_mass must be provided.")
      else:
        dry_mass = total_mass - sum(resource_tons.values())
        assert_equal(dry_mass + sum(resource_tons.values()), total_mass)
    
    self.speed, self.resource_tons, self.dry_mass = (speed, resource_tons, dry_mass)
    self.time_burned = 0.0
    self._validate()


  def _validate(self) -> None:
    assert self.time_burned is None or self.time_burned >= 0
    assert all(item >= 0 for item in (self.speed, self.dry_mass)), "one or more of the ship's dry mass or speed is/went negative."
    assert all(tons >= 0 for tons in self.resource_tons.values()), "a resource mass is/went negative."


  def get_mass(self) -> numbers.Real:
    return self.dry_mass + sum(self.resource_tons.values())


  def isru(self, *, ore_tons: numbers.Real, mode) -> None:
    if ore_tons < 0:
      raise ValueError("a zero or positive amount of ore must be used.")
    if ore_tons > self.resource_tons[ORE]:
      raise ValueError(f"{ore_tons} is more ore than you have, {self.resource_tons[ORE]}.") 
    match mode:
      case "lf":
        self.resource_tons[ORE], self.resource_tons[LF] = (self.resource_tons[ORE] - ore_tons, self.resource_tons[LF] + ore_tons)
      case "ox":
        self.resource_tons[ORE], self.resource_tons[OX] = (self.resource_tons[ORE] - ore_tons, self.resource_tons[OX] + ore_tons)
      case "lfox":
        self.resource_tons[ORE], self.resource_tons[LF], self.resource_tons[OX] = (
          self.resource_tons[ORE] - ore_tons,
          (self.resource_tons[LF] + ore_tons*KSP_LFOX_COEFFICIENTS[0]),
          (self.resource_tons[OX] + ore_tons*KSP_LFOX_COEFFICIENTS[1]),
        )
      case "monopropellant":
        raise NotImplementedError("monopropellant isru mode.")
      case _:
        raise ValueError(f"unknown isru mode {mode}.")
    self._validate()

  
  def burn(self, *, propellant_tons: dict[Resource, numbers.Real], engine) -> None:
    if propellant_tons < 0:
      raise ValueError("a zero or positive amount of propellant must be burned.")
    if isinstance(engine, tuple):
      if len(engine) != 2:
        raise ValueError("invalid definition of engine.")
      Isp, mode = engine
    elif isinstance(engine, Engine):
      raise NotImplementedError()
    else:
      raise TypeError("invalid engine or group of engines or something.")
    if Isp < 0:
      raise ValueError("Isp must be positive.")
      
    raise NotImplementedError("burn will call _burn")
  
  
  def _burn(self, *, resource_tons, Isp, resource_flow_rates) -> None:
    propellantTonsUsed = sum(resource_tons.values())
    if resource_flow_rates is None:
      # print("_burn: warning: no resource_flow_rates provided, time_burned will be set to None.")
      self.time_burned = None
    else:
      if not set(resource_tons.keys()) == set(resource_flow_rates.keys()):
        raise ValueError("the resources in resource_tons and resource_flow_rates are not the same.")
      propellantTonsUsedPerSecond = sum(resource_flow_rates.values())
      burnTime = propellantTonsUsed / propellantTonsUsedPerSecond
      if self.time_burned is not None:
        self.time_burned += burnTime
      for key, value in resource_flow_rates.items():
        if not value - resource_tons[key] < ERROR_TOLERANCE_TONS:
          raise ValueError("resource_flow_rates cannot account for resource_tons.")
    self.speed += tsiolkovsky(Isp, self.get_mass(), self.get_mass()-propellantTonsUsed)
    subtract_dictionary_vector_in_place(self.resource_tons, resource_tons)
    self._validate()
    
_a = Ship(resource_tons={Resource.ORE:2, Resource.LIQUID_FUEL:0}, dry_mass=30)
assert _a.get_mass() == 32
_a.isru(ore_tons=0.9, mode="lf")
assert _a.resource_tons[Resource.LIQUID_FUEL] == 0.9
assert _a.resource_tons[Resource.ORE] == 1.1
assert _a.get_mass() == 32
assert _a.speed == 0.0
_a._burn(resource_tons={LF:0.5}, Isp=100, resource_flow_rates={LF:0.1})
assert _a.time_burned == 5
assert _a.resource_tons[LF] == 0.4
assert _a.speed > 0
del _a
_b = Ship(resource_tons={LF:1}, dry_mass=1)
_b._burn(resource_tons={LF:1}, Isp=100, resource_flow_rates=None)
assert _b.time_burned is None
del _b