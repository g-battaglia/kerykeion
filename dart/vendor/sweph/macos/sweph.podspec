#
# To learn more about a Podspec see http://guides.cocoapods.org/syntax/podspec.html.
# Run `pod lib lint sweph.podspec` to validate before publishing.
#
Pod::Spec.new do |s|
  s.name             = 'sweph'
  s.version          = '3.2.1+2.10.3'
  s.summary          = 'Cross-platform bindings of Swiss Ephemeris APIs for Flutter.'
  s.description      = <<-DESC
Cross-platform bindings of Swiss Ephemeris APIs for Flutter.
                       DESC
  s.homepage         = 'https://github.com/vm75/sweph.dart'
  s.license          = { :file => '../LICENSE' }
  s.author           = { 'VM75' => 'vm75.dev@gmail.com' }

  # This will ensure the source files in Classes/ are included in the native
  # builds of apps using this FFI plugin. Podspec does not support relative
  # paths, so Classes contains a forwarder C file that relatively imports
  # `../native/*` so that the C sources can be shared among all target platforms.
  s.source           = { :path => '.' }
  s.source_files     = 'Classes/**/*'
  s.dependency 'FlutterMacOS'

  s.platform = :osx, '10.11'
  s.pod_target_xcconfig = { 'DEFINES_MODULE' => 'YES' }
  s.swift_version = '5.0'
end
