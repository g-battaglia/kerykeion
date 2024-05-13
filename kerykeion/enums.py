from enum import Enum


class Planets(Enum):
    SUN = "Sun"
    MOON = "Moon"
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"
    CHIRON = "Chiron"
    TRUE_NODE = "True_Node"
    MEAN_NODE = "Mean_Node"


class Aspects(Enum):
    CONJUNCTION = "Conjunction"
    SEXTILE = "Sextile"
    SEMI_SEXTILE = "Semi-Sextile"
    SQUARE = "Square"
    TRINE = "Trine"
    OPPOSITION = "Opposition"
    QUINCUNX = "Quincunx"
    NONE = None
    QUINTILE = "Quintile"
    BIQUINTILE = "Biquintile"
    OCTILE = "Octile"
    TRIOCTILE = "Trioctile"
    DECILE = "Decile"
    TRIDECILE = "Tridecile"
    SESQUIQUADRATE = "Sesquiquadrate"


class Signs(Enum):
    ARI = "Ari"
    TAU = "Tau"
    GEM = "Gem"
    CAN = "Can"
    LEO = "Leo"
    VIR = "Vir"
    LIB = "Lib"
    SCO = "Sco"
    SAG = "Sag"
    CAP = "Cap"
    AQU = "Aqu"
    PIS = "Pis"
