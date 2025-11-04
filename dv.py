
import math



LFOX_RATIO_PARTS = (9,11)
LFOX_COEFFICIENTS = tuple(item/sum(LFOX_RATIO_PARTS) for item in LFOX_RATIO_PARTS) 
STANDARD_GRAVITY = 9.80665


def tsiolkovsky(Isp, m0, mf):
  assert 0 < Isp
  assert 0 < mf < m0
  return Isp*STANDARD_GRAVITY*math.log(m0/mf)


class Engine:

  def __init__(self, *, Isp_vacuum, thrust_kn, flow_rates=None):
    self.Isp_vacuum, self.thrust_kn = (Isp_vacuum, thrust_kn)
    self.flow_rates = ...


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
          (self.lf_tons + ore_tons*LFOX_COEFFICIENTS[0]),
          (self.ox_tons + ore_tons*LFOX_COEFFICIENTS[1]),
        )
      case _:
        raise ValueError(f"unknown mode {mode}")
    self._validate()

  
  def burn(self, *, propellant_tons, Isp, mode):
    assert 0 <= propellant_tons
    assert 0 <= Isp
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