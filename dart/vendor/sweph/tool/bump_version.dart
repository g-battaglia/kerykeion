// ignore_for_file: avoid_print

import 'dart:convert';
import 'dart:io';

List<String> getopt(String parseOptions, List<String> args) {
  final optString = ',$parseOptions,';
  var stopParsing = false;
  final List<String> options = [];
  final List<String> result = [];
  outer:
  while (args.isNotEmpty) {
    final nextArg = args.removeAt(0);
    if (nextArg == '--') {
      stopParsing = true;
      continue;
    }

    if (!stopParsing && nextArg.isNotEmpty) {
      switch (nextArg) {
        case '--d':
          continue outer;
        case '--t':
          continue outer;
        case '--h':
          continue outer;
      }
      if (optString.contains(RegExp('.*,$nextArg:,.*'))) {
        options.add(nextArg);
        if (args.isNotEmpty) {
          options.add(args.removeAt(0));
        }
        continue outer;
      } else if (optString.contains(RegExp('.*,$nextArg,.*'))) {
        options.add(nextArg);
        continue outer;
      }
    }
    result.add(nextArg);
  }
  if (parseOptions.isEmpty) {
    return result;
  } else {
    options.add('--');
    options.addAll(result);
    return options;
  }
}

const versionRegex = r'(?:(\d+)\.(\d+)\.(\d+)(?:\+(.+))?)';

enum BumpType { major, minor, patch }

class Version {
  final int _major;
  final int _minor;
  final int _patch;
  final String? _buildNumber;

  Version(this._major, this._minor, this._patch, [this._buildNumber]);

  static Version? fromString(String? versionStr, [String? buildNumber]) {
    final RegExp pattern = RegExp('^$versionRegex\$');

    if (versionStr == null || !pattern.hasMatch(versionStr)) {
      return null;
    }

    final match = pattern.firstMatch(versionStr)!;
    final major = int.parse(match.group(1)!);
    final minor = int.parse(match.group(2)!);
    final patch = int.parse(match.group(3)!);
    buildNumber ??= match.group(4);

    return Version(major, minor, patch, buildNumber);
  }

  static Version? fromFile(String filePath, [String? prefix, String? suffix]) {
    final file = File(filePath);
    if (!file.existsSync()) {
      print('File not found: $filePath');
      return null;
    }

    final RegExp pattern =
        RegExp('${prefix ?? ''}($versionRegex)${suffix ?? ''}');

    for (final line in file.readAsLinesSync()) {
      final match = pattern.firstMatch(line);
      if (match == null) {
        continue;
      }
      return fromString(match.group(1));
    }
    return null;
  }

  @override
  String toString() {
    if (_buildNumber == null) {
      return '$_major.$_minor.$_patch';
    } else {
      return '$_major.$_minor.$_patch+$_buildNumber';
    }
  }

  Version bump(BumpType bumpType, [String? buildNumber]) {
    switch (bumpType) {
      case BumpType.major:
        return Version(_major + 1, 0, 0, buildNumber ?? _buildNumber);
      case BumpType.minor:
        return Version(_major, _minor + 1, 0, buildNumber ?? _buildNumber);
      case BumpType.patch:
        return Version(_major, _minor, _patch + 1, buildNumber ?? _buildNumber);
    }
  }
}

class VersionFileSpec {
  final String filePath;
  final String? prefix;
  final String? suffix;

  VersionFileSpec(this.filePath, [this.prefix, this.suffix]);

  Version? getVersion() => Version.fromFile(filePath, prefix, suffix);
}

class VersionUpdateHelper {
  final String? _buildCode;
  final Version _currentVersion;
  final List<String> _changelogs = [];
  bool _versionInBraces = true;
  String _tab = '*';
  final Map<String, List<String>> _filesWithVersion = {};
  final List<String> _filesWithChangelogs = [];

  factory VersionUpdateHelper(
    VersionFileSpec versionFile, [
    VersionFileSpec? buildFile,
  ]) {
    final version = versionFile.getVersion();
    if (version == null) {
      throw Exception('Version not found in ${versionFile.filePath}');
    }
    final build = buildFile?.getVersion();
    if (buildFile != null && build == null) {
      throw Exception('Build version not found in ${buildFile.filePath}');
    }

    return VersionUpdateHelper._(version, build?.toString());
  }

  VersionUpdateHelper._(this._currentVersion, this._buildCode);

  String currentVersion() => _currentVersion.toString();

  void addFilesWithVersion(String prefix, List<String> files) {
    _filesWithVersion[prefix] = files;
  }

  void addFilesWithChangelog(List<String> files) {
    _filesWithChangelogs.addAll(files);
  }

  void setChangelog(
    List<String> changelogs, {
    bool? versionInBraces,
    String? tab,
  }) {
    var changeLogs = changelogs;
    if (changelogs.isEmpty) {
      changeLogs = _getChangelogs();
      if (changeLogs.isEmpty) {
        throw Exception('No changelog provided');
      }
    }
    _changelogs.addAll(changeLogs);
    _versionInBraces = versionInBraces ?? _versionInBraces;
    _tab = tab ?? _tab;
  }

  static String _changelogToString(
    Version version,
    List<String> changelogs, {
    bool versionInBraces = true,
    String tab = '*',
  }) {
    final log = StringBuffer();

    log.write(versionInBraces ? '## [$version]\n' : '## $version\n');
    for (final changelog in changelogs) {
      log.write('$tab $changelog\n');
    }
    log.write('\n');
    return log.toString();
  }

  static List<String> _getChangelogs() {
    final changelogs = <String>[];
    print('Enter changelogs (empty line to stop):');
    while (true) {
      final line = stdin.readLineSync();
      if (line == null || line.trim().isEmpty || line.trim() == '.') {
        break;
      }
      changelogs.add(line.trim());
    }
    return changelogs;
  }

  static void _replaceInFiles(
    List<String> files,
    String from,
    String to, [
    String? prefix,
  ]) {
    final String prefixedFrom = prefix != null ? prefix + from : from;
    final String prefixedTo = prefix != null ? prefix + to : to;

    for (final filePath in files) {
      final bool isCMakefile = filePath.endsWith('CMakeLists.txt');
      final file = File(filePath);
      var contents = file.readAsStringSync();
      if (isCMakefile) {
        contents = contents.replaceAll(
            prefixedFrom.split('+')[0], prefixedTo.split('+')[0]);
      } else {
        contents = contents.replaceAll(prefixedFrom, prefixedTo);
      }
      file.writeAsStringSync(contents);
    }
  }

  static void _prependToFiles(List<String> files, String prefix) {
    for (final filePath in files) {
      final file = File(filePath);
      try {
        final contents = file.readAsStringSync();
        file.writeAsStringSync(prefix + contents);
      } catch (e) {
        print('Failed to update $filePath: $e');
      }
    }
  }

  void _bump(Version nextVersion) {
    final from = _currentVersion.toString();
    final to = nextVersion.toString();

    // Update version in files
    for (final entry in _filesWithVersion.entries) {
      _replaceInFiles(entry.value, from, to, entry.key);
    }

    // Update changelogs
    if (_changelogs.isEmpty) {
      return;
    }
    if (_changelogs.isEmpty) {
      throw Exception('No changelogs specified');
    }
    _prependToFiles(
      _filesWithChangelogs,
      _changelogToString(
        nextVersion,
        _changelogs,
        versionInBraces: _versionInBraces,
        tab: _tab,
      ),
    );

    print("Updated version from '$from' to $to");
    print("Commit log: ${_changelogs.join('. ')}");
  }

  void bump(BumpType bumpType) {
    final nextVersion = _currentVersion.bump(bumpType, _buildCode);
    return _bump(nextVersion);
  }

  void setNextVersion(String nextVersionStr) {
    final nextVersion = Version.fromString(nextVersionStr);

    if (nextVersion == null) {
      throw Exception('Invalid version: $nextVersionStr');
    }

    return _bump(nextVersion);
  }
}

void main(List<String> args) {
  final opts = getopt('patch,major,minor,log:,help', args.toList());
  BumpType? bumpType;

  final List<String> changeLogs = [];
  while (opts.isNotEmpty) {
    final String opt = opts.removeAt(0);
    if (opt == '--') {
      break;
    }
    switch (opt) {
      case 'major':
        bumpType = BumpType.major;
        break;
      case 'minor':
        bumpType = BumpType.minor;
        break;
      case 'patch':
        bumpType = BumpType.patch;
        break;
      case 'log':
        changeLogs.add(opts.removeAt(0));
        break;
      case 'help':
        print('usage: bump_version [major|minor|patch|log <message>|help]');
        exit(0);
    }
  }

  try {
    final helper = VersionUpdateHelper(
      VersionFileSpec(
        'pubspec.yaml',
        'version: ',
      ),
      VersionFileSpec(
        'native/sweph/src/sweph.h',
        '^#define SE_VERSION\\s+"',
        '"',
      ),
    );

    // Add files to update version
    helper.addFilesWithVersion(
      '\nversion: ',
      ['pubspec.yaml'],
    );
    helper.addFilesWithVersion(
      "\n  s.version          = '",
      ['ios/sweph.podspec', 'macos/sweph.podspec'],
    );
    helper.addFilesWithVersion(
      "\nversion '",
      ['android/build.gradle'],
    );
    helper.addFilesWithVersion(
      '} VERSION ',
      ['linux/CMakeLists.txt', 'windows/CMakeLists.txt'],
    );

    // Get changelogs
    helper.setChangelog(changeLogs);

    // Add files to update changelog
    helper.addFilesWithChangelog(['CHANGELOG.md']);

    // Get next version
    if (bumpType == null) {
      stdout.write('Enter version next to "${helper.currentVersion()}": ');
      final versionStr = stdin.readLineSync(encoding: utf8);
      if (versionStr == null || versionStr.isEmpty) {
        throw Exception('No version provided');
      }
      helper.setNextVersion(versionStr);
    } else {
      helper.bump(bumpType);
    }
  } on Exception catch (e) {
    print(e);
    exit(1);
  }
}
