
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
    self._validate()
    
  def _validate(self):
    print("validate is not implemented for Engine")
    
  def get_mass_flow_rate(self):
    if self.resource_flow_rates is None:
      raise ValueError("flow rates were not provided")
    return sum(tonnage for resource, tonnage in self.resource_flow_rates)


STOCK_ENGINES = {
  "Terrier": Engine(Isp=345, thrust_kn=60, resource_flow_rates=((Resource.LIQUID_FUEL, 1.596),(Resource.OXIDIZER, 1.951))),
  "Nerv": Engine(Isp=800, thrust_kn=60, resource_flow_rates=((Resource.LIQUID_FUEL, 1.53),)),
}



class Ship:

  def __init__(self, *, velocity=0.0, ore_tons=0.0, lf_tons=0.0, ox_tons=0.0, dry_mass):
    self.velocity, self.ore_tons, self.lf_tons, self.ox_tons, self.dry_mass = (velocity, ore_tons, lf_tons, ox_tons, dry_mass)
    self._validate()  


  def _validate(self):
    assert all(item >= 0 for item in (self.velocity, self.ore_tons, self.lf_tons, self.ox_tons, self.dry_mass)), "one or more of the ship's resource values or mass or velocity is/went negative."


  def get_mass(self):
    return self.dry_mass + self.ore_tons + self.lf_tons + self.ox_tons


  def isru(self, *, ore_tons, mode):
    if ore_tons < 0:
      raise ValueError("a zero or positive amount of ore must be used.")
    if ore_tons > self.ore_tons:
      raise ValueError(f"{ore_tons} is more ore than you have, {self.ore_tons}.")
    match mode:
      case "lf":
        self.ore_tons, self.lf_tons = (self.ore_tons - ore_tons, self.lf_tons + ore_tons)
      case "ox":
        self.ore_tons, self.ox_tons = (self.ore_tons - ore_tons, self.ox_tons + ore_tons)
      case "lfox":
        self.ore_tons, self.lf_tons, self.ox_tons = (
          self.ore_tons - ore_tons,
          (self.lf_tons + ore_tons*KSP_LFOX_COEFFICIENTS[0]),
          (self.ox_tons + ore_tons*KSP_LFOX_COEFFICIENTS[1]),
        )
      case _:
        raise ValueError(f"unknown mode {mode}")
    self._validate()

  
  def burn(self, *, propellant_tons, engine) -> None:
    if propellant_tons < 0:
      raise ValueError()
    if isinstance(engine, tuple):
      if len(engine) != 2:
        raise ValueError()
      Isp, mode = engine
    elif isinstance(engine, Engine):
      raise NotImplementedError()
    else:
      raise TypeError("invalid engine or group of engines or something.")
    if Isp < 0:
      raise ValueError("Isp must be positive")
    match mode:
      case "lf":
        if propellant_tons > self.lf_tons:
          raise ValueError("out of fuel.")
        self.velocity, self.lf_tons = (
          tsiolkovsky(Isp, self.get_mass(), self.get_mass()-propellant_tons),
          self.lf_tons - propellant_tons,
        )
      case "ox":
        raise NotImplementedError("what? an oxidizer-only engine?")
      case "lfox":
        raise NotImplementedError("unfinished code.")
      case _:
        raise ValueError(f"unknown mode {mode}")
    self._validate()