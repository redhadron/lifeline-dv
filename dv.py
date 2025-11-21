
import math
from enum import Enum


KSP_LFOX_RATIO_PARTS = (9,11)
KSP_LFOX_COEFFICIENTS = tuple(item/sum(KSP_LFOX_RATIO_PARTS) for item in KSP_LFOX_RATIO_PARTS) 
STANDARD_GRAVITY = 9.80665


def tsiolkovsky(Isp, m0, mf) -> float:
  assert 0 < Isp
  assert 0 < mf < m0
  return Isp*STANDARD_GRAVITY*math.log(m0/mf)


class Resource(Enum):
  LIQUID_FUEL = "LIQUID_FUEL"
  OXIDIZER = "OXIDIZER"
  ORE = "ORE"
  MONOPROPELLANT = "MONOPROPELLANT"
  XENON_GAS = "XENON_GAS"
  

class Engine:

  def __init__(self, *, Isp, thrust_kn, resource_flow_rates=None):
    self.Isp, self.thrust_kn = (Isp, thrust_kn)
    self.resource_flow_rates = resource_flow_rates
    
  def get_mass_flow_rate(self):
    if self.resource_flow_rates is None:
      raise ValueError("flow rates were not provided on Engine initialization.")
    return sum(self.resource_flow_rates.values()) # in tons


STOCK_ENGINES = {
  "Terrier": Engine(Isp=345, thrust_kn=60, resource_flow_rates={Resource.LIQUID_FUEL: 1.596, Resource.OXIDIZER: 1.951}),
  "Nerv": Engine(Isp=800, thrust_kn=60, resource_flow_rates={Resource.LIQUID_FUEL: 1.53}),
}



class Ship:

  def __init__(self, *, velocity=0.0, resource_tons, dry_mass):
    self.velocity, self.resource_tons, self.dry_mass = (velocity, resource_tons, dry_mass)
    self.time_burned = 0.0
    self._validate()  


  def _validate(self):
    assert all(item >= 0 for item in (self.velocity, self.dry_mass, self.time_burned)), "one or more of the ship's dry mass or velocity or time_burned is/went negative."
    assert all(tons >= 0 for tons in self.resource_tons.values()), "a resource mass is/went negative."


  def get_mass(self):
    return self.dry_mass + sum(self.resource_tons.values())


  def isru(self, *, ore_tons, mode):
    if ore_tons < 0:
      raise ValueError("a zero or positive amount of ore must be used.")
    if ore_tons > self.resource_tons[Resource.ORE]:
      raise ValueError(f"{ore_tons} is more ore than you have, {self.resource_tons[Resource.ORE]}.")
    match mode:
      case "lf":
        self.resource_tons[Resource.ORE], self.resource_tons[Resource.LIQUID_FUEL] = (self.resource_tons[Resource.ORE] - ore_tons, self.resource_tons[Resource.LIQUID_FUEL] + ore_tons)
      case "ox":
        self.resource_tons[Resource.ORE], self.resource_tons[Resource.OXIDIZER] = (self.resource_tons[Resource.ORE] - ore_tons, self.resource_tons[Resource.OXIDIZER] + ore_tons)
      case "lfox":
        self.resource_tons[Resource.ORE], self.resource_tons[Resource.LIQUID_FUEL], self.resource_tons[Resource.OXIDIZER] = (
          self.resource_tons[Resource.ORE] - ore_tons,
          (self.resource_tons[Resource.LIQUID_FUEL] + ore_tons*KSP_LFOX_COEFFICIENTS[0]),
          (self.resource_tons[Resource.OXIDIZER] + ore_tons*KSP_LFOX_COEFFICIENTS[1]),
        )
      case _:
        raise ValueError(f"unknown isru mode {mode}")
    self._validate()

  
  def burn(self, *, propellant_tons, engine) -> None:
    if propellant_tons < 0:
      raise ValueError("a zero or positive amount of propellant must be burned.")
    if isinstance(engine, tuple):
      if len(engine) != 2:
        raise ValueError("invalid definition of engine")
      Isp, mode = engine
    elif isinstance(engine, Engine):
      raise NotImplementedError()
    else:
      raise TypeError("invalid engine or group of engines or something.")
    if Isp < 0:
      raise ValueError("Isp must be positive")
    raise NotImplementedError("burn will call _burn")
  
  def _burn(self, *, resource_tons, Isp, resource_flow_rates=None):
    propellantTonsUsed = sum(resource_tons.values())
    # propellantTonsUsedPerSecond = sum(tons for resource, tons in resource_flow_rates.items())
    self.velocity = tsiolkovsky(Isp, self.get_mass(), self.get_mass()-propellantTonsUsed)
    raise NotImplementedError("resource consumption")
    
    self._validate()