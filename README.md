[![internal JetBrains project](https://jb.gg/badges/internal.svg)](https://confluence.jetbrains.com/display/ALL/JetBrains+on+GitHub)
# Automated Skia builds

> [!NOTE]
> Archived. The active Skiko prebuilts workflow now lives in [JetBrains/skia](https://github.com/JetBrains/skia).

This repo is dedicated to building Skia binaries for use in [Skiko](https://github.com/JetBrains/skiko).

## Prebuilt binaries

Prebuilt binaries can be found [in releases](https://github.com/JetBrains/skia-pack/releases).

## Building next version of Skia

1. Find the release commit in [Skia repository](https://github.com/google/skia) (look for chrome/mXXX branch)
2. Rebase `skiko` branch in [Skia fork repository](https://github.com/JetBrains/skia) on this commit and force push
3. Update `version` in [.github/workflows/build.yml](https://github.com/JetBrains/skia-pack/blob/master/.github/workflows/build.yml).

## Building locally
Replace SKIA_VERSION with the version you want to build, for example `m138-9e6b5bff162`.
Note: Better check build.yml for the detailed command for your machine

```sh
python3 script/checkout.py --version SKIA_VERSION
python3 script/build.py
python3 script/archive.py --version SKIA_VERSION
```

To build a debug build:

```sh
python3 script/checkout.py --version SKIA_VERSION
python3 script/build.py --build-type Debug
python3 script/archive.py --version SKIA_VERSION --build-type Debug
```

### FreeType

Every target is built with FreeType, statically compiled from the bundled
`third_party/externals/freetype` sources (`skia_use_freetype=true`,
`skia_use_system_freetype2=false`), so no system FreeType package is required on
the build machine.

Skia only enables FreeType by itself on android/linux/wasm, so the build script
passes it explicitly for windows/macos/ios/tvos. Enabling it adds the FreeType
font managers (`SkFontMgr_custom_directory`/`_embedded`/`_empty`,
`SkTypeface_FreeType`) to Skia; the default platform font manager is unchanged
(DirectWrite on Windows, CoreText on Apple platforms, fontconfig on Linux).

The prebuilt artifacts contain `freetype2.lib`/`libfreetype2.a` and the FreeType
headers (`third_party/externals/freetype/include`, plus the build configuration
headers from `third_party/freetype2/include`). FreeType is a separate static
library from Skia, so a consumer that uses the FreeType font managers or `FT_*`
APIs directly must add it to its link inputs.

To build without FreeType, pass `--freetype false` (or `--no-freetype`):

```sh
python3 script/build.py --freetype false
```

### Windows-specific

On Windows, skia-pack requires Clang-cl to be installed. Clang-cl is a part of LLVM and can be downloaded from the [LLVM project's website](https://releases.llvm.org/). Please also make sure that Clang-cl.exe is available on %PATH%.
