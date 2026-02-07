import 'package:kerykeion_dart/src/types.dart';
import 'package:kerykeion_dart/src/models/zodiac_sign.dart';

const Map<int, ZodiacSignModel> zodiacSigns = {
  0: ZodiacSignModel(sign: Sign.Ari, quality: Quality.Cardinal, element: Element.Fire, emoji: "♈️", signNum: 0),
  1: ZodiacSignModel(sign: Sign.Tau, quality: Quality.Fixed, element: Element.Earth, emoji: "♉️", signNum: 1),
  2: ZodiacSignModel(sign: Sign.Gem, quality: Quality.Mutable, element: Element.Air, emoji: "♊️", signNum: 2),
  3: ZodiacSignModel(sign: Sign.Can, quality: Quality.Cardinal, element: Element.Water, emoji: "♋️", signNum: 3),
  4: ZodiacSignModel(sign: Sign.Leo, quality: Quality.Fixed, element: Element.Fire, emoji: "♌️", signNum: 4),
  5: ZodiacSignModel(sign: Sign.Vir, quality: Quality.Mutable, element: Element.Earth, emoji: "♍️", signNum: 5),
  6: ZodiacSignModel(sign: Sign.Lib, quality: Quality.Cardinal, element: Element.Air, emoji: "♎️", signNum: 6),
  7: ZodiacSignModel(sign: Sign.Sco, quality: Quality.Fixed, element: Element.Water, emoji: "♏️", signNum: 7),
  8: ZodiacSignModel(sign: Sign.Sag, quality: Quality.Mutable, element: Element.Fire, emoji: "♐️", signNum: 8),
  9: ZodiacSignModel(sign: Sign.Cap, quality: Quality.Cardinal, element: Element.Earth, emoji: "♑️", signNum: 9),
  10: ZodiacSignModel(sign: Sign.Aqu, quality: Quality.Fixed, element: Element.Air, emoji: "♒️", signNum: 10),
  11: ZodiacSignModel(sign: Sign.Pis, quality: Quality.Mutable, element: Element.Water, emoji: "♓️", signNum: 11),
};

const Map<AstrologicalPoint, int> pointNumberMap = {
  // Standard planets (0-9)
  AstrologicalPoint.Sun: 0,
  AstrologicalPoint.Moon: 1,
  AstrologicalPoint.Mercury: 2,
  AstrologicalPoint.Venus: 3,
  AstrologicalPoint.Mars: 4,
  AstrologicalPoint.Jupiter: 5,
  AstrologicalPoint.Saturn: 6,
  AstrologicalPoint.Uranus: 7,
  AstrologicalPoint.Neptune: 8,
  AstrologicalPoint.Pluto: 9,

  // Lunar nodes (10-11)
  AstrologicalPoint.Mean_North_Lunar_Node: 10,
  AstrologicalPoint.True_North_Lunar_Node: 11,

  // South nodes (calculated as opposite of north nodes)
  AstrologicalPoint.Mean_South_Lunar_Node: 1000,
  AstrologicalPoint.True_South_Lunar_Node: 1100,

  // Lilith points (12-13)
  AstrologicalPoint.Mean_Lilith: 12,
  AstrologicalPoint.True_Lilith: 13,

  // Earth and Centaurs (14-16)
  AstrologicalPoint.Earth: 14,
  AstrologicalPoint.Chiron: 15,
  AstrologicalPoint.Pholus: 16,

  // Main belt asteroids (17-20)
  AstrologicalPoint.Ceres: 17,
  AstrologicalPoint.Pallas: 18,
  AstrologicalPoint.Juno: 19,
  AstrologicalPoint.Vesta: 20,

  // Trans-Neptunian Objects (TNOs) - use asteroid numbers
  AstrologicalPoint.Ixion: 28978,
  AstrologicalPoint.Quaoar: 50000,
  AstrologicalPoint.Sedna: 90377,
  AstrologicalPoint.Orcus: 90482,
  AstrologicalPoint.Haumea: 136108,
  AstrologicalPoint.Eris: 136199,
  AstrologicalPoint.Makemake: 136472,

  // Angles (9900-9903) - calculated from house cusps
  AstrologicalPoint.Ascendant: 9900,
  AstrologicalPoint.Descendant: 9901,
  AstrologicalPoint.Medium_Coeli: 9902,
  AstrologicalPoint.Imum_Coeli: 9903,

  // Note: Fixed stars (Regulus, Spica) use swe_fixstar_ut() instead
  // Note: Arabic parts (Pars_*) are calculated mathematically
  // Note: Vertex/Anti_Vertex are calculated from house cusps
};

// House name mappings
const Map<int, House> houseNames = {
  1: House.First_House,
  2: House.Second_House,
  3: House.Third_House,
  4: House.Fourth_House,
  5: House.Fifth_House,
  6: House.Sixth_House,
  7: House.Seventh_House,
  8: House.Eighth_House,
  9: House.Ninth_House,
  10: House.Tenth_House,
  11: House.Eleventh_House,
  12: House.Twelfth_House,
};

const Map<House, int> houseNumbers = {
  House.First_House: 1,
  House.Second_House: 2,
  House.Third_House: 3,
  House.Fourth_House: 4,
  House.Fifth_House: 5,
  House.Sixth_House: 6,
  House.Seventh_House: 7,
  House.Eighth_House: 8,
  House.Ninth_House: 9,
  House.Tenth_House: 10,
  House.Eleventh_House: 11,
  House.Twelfth_House: 12,
};
