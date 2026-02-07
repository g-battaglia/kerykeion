## [3.2.1+2.10.3]
* Add topics

## [3.2.0+2.10.3]
* Updated universal_ffi to version 1.1.0

## [3.1.0+2.10.3]
* migrated to universl_ffi

## [3.0.2+2.10.3]
* Updated example to latest template. added additional asset for init.

## [3.0.1+2.10.3]
* Made init friendler for flutter

## [3.0.0+2.10.3]
* Converting to pure dart package. Some changes to init and example. Modified versioning format. Now including sweph version as build number.

## [2.10.3+18]
* Corrected swe_house_pos method parameters

## [2.10.3+17]
* Breaking Change! Fixed swe_rise_trans and swe_rise_trans_true_hor exception and return. Modified target parameter for 6 commands. These commands now take a single parameter which could be either HeavenlyBody or Star name as string

## [2.10.3+16]
* Fixing return values for some calls. Also adding doc comments.

## [2.10.3+15]
* updating MacOS and iOS build files

## [2.10.3+14]
* Update version after fixing #10

## [2.10.3+13]
* Fixing build error due to some missed int -> int32 changes

## [2.10.3+12]
* fixing int type to int32 for web compatibility

## [2.10.3+11]
* fixed type for swe_set_sid_mode

## [2.10.03+10]
* fixed RiseSetTransitFlag. added bump_version script

## [2.10.03+9]
* Replaced web_ffi with wasm_ffi

## [2.10.03+8]
* Fixed readme and SDK range

## [2.10.03+7]
* Added support for Web. Some more refactoring.

## [2.10.03+6]
* Tentative fix for iOS which is still failing.

## [2.10.03+5]
* Fixed example for mobile devices.

## [2.10.03+4]
* Reverting recent changes :( and making swe_set_ephe_path & swe_set_jpl_file public again.
* Fixed init sequence so that Sweph can be used in sync as well as async mode.

## [2.10.03+3]
* Added swe_set_jpl_file to init since ephe-path and jpl-file cannot be updated.
* Made swe_set_ephe_path & swe_set_jpl_file private.
* Breaking changes to instance creation since 2.10.03+1.

## [2.10.03+2]
* Fixed init to handle ephe-path correctly. Fixed array size in house-system calls. Updated example.

## [2.10.03+1]
* Updated sweph to upstream version 2.10.03.

## [2.10.02+9]
* Hopefully fixed compilation for ios/mac (untested).

## [2.10.02+8]
* Updated readme with some more examples

## [2.10.02+7]
* Updated Changelog

## [2.10.02+6]
* Fixed readme

## [2.10.02+5]
* Updated comments

## [2.10.02+4]
* changed appDir to getApplicationSupportDirectory. added comments

## [2.10.02+3]
* Fixed Linux build.

## [2.10.02+2]
* readme fix again

## [2.10.02+2]
* Fixed readme

## [2.10.02+1]
* Initial release with Swiss Ephemeris version 2.10.02
