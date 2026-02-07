# Sweph

Cross-platform bindings of Swiss Ephemeris APIs for Dart & Flutter.
Everything you need to create Astrology and Astronomy applications with Dart and Flutter.

* 100% API coverage
* Dart friendly parameters and return values
* Supported on all platforms. Uses ffi for non-Web platforms and [wasm_ffi](https://pub.dev/packages/wasm_ffi) for Web
* Original Swiss Ephemeris version used as build number for reference

References:
- [Official programmers documentation for the Swiss Ephemeris by Astrodienst AG](https://www.astro.com/swisseph/swephprg.htm)
- [Official guide for the Swiss Ephemeris by Astrodienst AG](https://www.astro.com/ftp/swisseph/doc/swisseph.htm)
- [Official site for source and ehemeris files](https://www.astro.com/ftp/swisseph/)
- [Sweph for Flutter on Github](https://github.com/vm75/sweph.dart)
- [Sweph on pub.dev](https://pub.dev/packages/sweph)

## Usage example
```dart
import 'package:sweph/sweph.dart';

Future<void> main() async {
  // Sweph comes bundled with some ephe file. These are available for Flutter but not for vanilla Dart
  // These or any other bundled ephe files can be initialized during Sweph init
  // These are coped to <ApplicationSupportDirectory>/ephe_files folder for non-Web platforms
  // For Web, this is the only way to provide ephe files, and they are loaded into memory
  await Sweph.init(
    modulePath: 'sweph', // where to load module from.
    epheAssets: [
      "packages/sweph/assets/ephe/sefstars.txt",
    ],
    assetLoader: SomeLoader(), // platform-specific asset loader.
    epheFilesPath: 'ephe_files', // where to store ephe files.
  );
  // refer to example. Both Flutter and vanilla Dart examples are available

  // alternately if a folder already contains ephe files, Sweph can be used in sync mode like this:
  // await Sweph.swe_set_ephe_path(<path-to-existing-folder>)
  // This is not available for Web

  print('sweph.swe_version = ${Sweph.swe_version()}');
  print('Moon longitude on 2022-06-29 02:52:00 UTC = ${Sweph.swe_calc_ut(Sweph.swe_julday(2022, 6, 29, (2 + 52 / 60), CalendarType.SE_GREG_CAL), HeavenlyBody.SE_MOON, SwephFlag.SEFLG_SWIEPH).longitude}');

  // Most methods use positional parameters, not named. So if some positional parameters take default values, please refer to original documentation
  // If only some specific flags are allowed for a method, it is restricted via the enumerated flags
  // For example, to set the sidereal mode to Lahiri with projection onto solar system plane and custom t0 in UT
  Sweph.swe_set_sid_mode(SiderealMode.SE_SIDM_LAHIRI, SiderealModeFlag.SE_SIDBIT_SSY_PLANE, 123.45 /* t0 */);
  // or, to set the sidereal mode to Lahiri with no flags and custom ayan_t0 in UT
  Sweph.swe_set_sid_mode(SiderealMode.SE_SIDM_LAHIRI, SiderealModeFlag.SE_SIDBIT_NONE, 0.0 /* t0 */, 987.65 /* ayan_t0 */);
}
```

## Licensing

This library follows the licensing requirements for the Swiss Ephemeris by Astrodienst AG.

### - AGPL

Starting from version `2.10.02` and later, this library is licensed under `AGPL-3.0`.
To install and use the latest version of this library under AGPL, use `flutter pub add sweph`.

### - LGPL

If you own a professional license for the Swiss Ephemeris, you may use any version of this library under `LGPL-3.0`.

## Versioning

The Swiss Ephemeris version string is used as a build number in the version.

## Ephemeris files

The following ephemeris files are bundled with this plugin:
  * seas_18.se1    - main ephemeris for asteroids (1800-2400 CE)
  * semo_18.se1    - main ephemeris for moon (1800-2400 CE)
  * sepl_18.se1    - main ephemeris for planets (1800-2400 CE)
  * seasnam.txt    - list of asteroids
  * sefstars.txt   - fixed stars data file
  * seleapsec.txt  - dates of leap seconds to be taken into account
  * seorbel.txt    - orbital elements of ficticious planets :)

These could also be download from [https://www.astro.com/ftp/swisseph/ephe/](https://www.astro.com/ftp/swisseph/ephe/).
More information can be found in the [Swiss Ephemeris files documentation](https://www.astro.com/ftp/swisseph/doc/swisseph.htm#_Toc58931065).

## Using bundled Ephemeris files
Sweph.init accepts a list of ephemeris files as assets. These could be any of the bundled ones or other app assets. It does not accept local file path!
### non-Web
These are cached in \<ApplicationSupportDirectory\>/ephe_files folder. First load will be slow.
Async methods swe_set_ephe_path & swe_set_jpl_file could be called to set new ephe files.
If file already present, it is not overwritten, unless  forceOverwrite is true.
### Web
Sweph.init is the only way to provide ephe files, and they are loaded into memory. This is a limitation of the Web plugin.
Calls to swe_set_ephe_path has no effect on Web. Only the loaded assets are used.
If custom JPL files are needed, the need to be loaded as with the name "jpl_file.eph" during init and swe_set_jpl_file could be called.

## Contributing

If you find any innacuracy or bug in this library, or if you find an update that is not yet included in this library, feel free to open an issue or a pull request.

## Known Issues and Caveats

* The included ephe files are available async only
* Due to how the underlying C library operates, you may find that the `error` field returned by some functions will contain random data even if there is no actual error. This can happen when existing memory buffers are recycled therefore the user must always check the returned flag values as per the Swiss Ephemeris documentation.

## Author

Copyright © 2022, VM75
