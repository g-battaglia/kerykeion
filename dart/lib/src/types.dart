enum ZodiacType { Tropical, Sidereal }

enum Sign { Ari, Tau, Gem, Can, Leo, Vir, Lib, Sco, Sag, Cap, Aqu, Pis }

enum AspectMovementType { Applying, Separating, Static }

enum House {
  First_House,
  Second_House,
  Third_House,
  Fourth_House,
  Fifth_House,
  Sixth_House,
  Seventh_House,
  Eighth_House,
  Ninth_House,
  Tenth_House,
  Eleventh_House,
  Twelfth_House,
}

enum AstrologicalPoint {
  Sun,
  Moon,
  Mercury,
  Venus,
  Mars,
  Jupiter,
  Saturn,
  Uranus,
  Neptune,
  Pluto,
  Mean_North_Lunar_Node,
  True_North_Lunar_Node,
  Mean_South_Lunar_Node,
  True_South_Lunar_Node,
  Chiron,
  Mean_Lilith,
  True_Lilith,
  Earth,
  Pholus,
  Ceres,
  Pallas,
  Juno,
  Vesta,
  Eris,
  Sedna,
  Haumea,
  Makemake,
  Ixion,
  Orcus,
  Quaoar,
  Regulus,
  Spica,
  Pars_Fortunae,
  Pars_Spiritus,
  Pars_Amoris,
  Pars_Fidei,
  Vertex,
  Anti_Vertex,
  Ascendant,
  Medium_Coeli,
  Descendant,
  Imum_Coeli,
}

enum Element { Air, Fire, Earth, Water }

enum Quality { Cardinal, Fixed, Mutable }

enum PointType { AstrologicalPoint, House }

enum LunarPhaseEmoji { New_Moon, Waxing_Crescent, First_Quarter, Waxing_Gibbous, Full_Moon, Waning_Gibbous, Last_Quarter, Waning_Crescent }

enum LunarPhaseName { New_Moon, Waxing_Crescent, First_Quarter, Waxing_Gibbous, Full_Moon, Waning_Gibbous, Last_Quarter, Waning_Crescent }

enum SiderealMode {
  FAGAN_BRADLEY,
  LAHIRI,
  DELUCE,
  RAMAN,
  USHASHASHI,
  KRISHNAMURTI,
  DJWHAL_KHUL,
  YUKTESHWAR,
  JN_BHASIN,
  BABYL_KUGLER1,
  BABYL_KUGLER2,
  BABYL_KUGLER3,
  BABYL_HUBER,
  BABYL_ETPSC,
  ALDEBARAN_15TAU,
  HIPPARCHOS,
  SASSANIAN,
  J2000,
  J1900,
  B1950,
}

enum HousesSystemIdentifier { A, B, C, D, E, F, H, I, i, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y }

enum PerspectiveType { Apparent_Geocentric, Heliocentric, Topocentric, True_Geocentric }

enum ChartType { Natal, Synastry, Transits, Composite, SingleReturnChart }

enum ReturnType { Lunar, Solar }
