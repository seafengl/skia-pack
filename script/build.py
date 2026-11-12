#! /usr/bin/env python3

import common, os, shutil, subprocess, sys

def ninja_path(host, host_machine):
  # depot_tools/ninja.bat on Windows is only a shim over depot_tools' own python
  # bootstrap (python3_bin_reldir.txt), which a freshly cloned depot_tools does
  # not have, so it fails with "python3_bin_reldir.txt not found". checkout.py
  # already runs skia/bin/fetch-ninja, which puts the DEPS-pinned binary into
  # third_party/ninja, so use that one there.
  if 'windows' == host:
    return os.path.join('third_party', 'ninja', 'ninja.exe')
  if 'linux' == host and 'arm64' == host_machine:
    return os.path.join('..', 'tools', 'ninja-linux-arm64')
  return os.path.join('..', 'depot_tools', 'ninja')

def gn_args(build_type, machine, target, host, host_machine, ndk, freetype):
  isIos = 'ios' == target or 'iosSim' == target
  isTvos = 'tvos' == target or 'tvosSim' == target
  isIosSim = 'iosSim' == target
  isTvosSim = 'tvosSim' == target
  isMacos = 'macos' == target

  if build_type == 'Debug':
    args = ['is_debug=true']
  else:
    args = ['is_official_build=true']

  args += [
    'target_cpu="' + machine + '"',
    'skia_use_system_expat=false',
    'skia_use_system_libjpeg_turbo=false',
    'skia_use_system_libpng=false',
    'skia_use_system_libwebp=false',
    'skia_use_system_zlib=false',
    'skia_use_system_harfbuzz=false',
    'skia_pdf_subset_harfbuzz=true',
    'skia_use_system_icu=false',
    'skia_enable_skottie=true',

    # Just to make following "+=" work unconditionally
    'extra_cflags=[]',
    'extra_cflags_cc=[]',
  ]

  # Skia enables FreeType only on android/linux/wasm by default, so it has to be
  # requested explicitly for windows/macos/ios/tvos. It is always built from the
  # bundled third_party/externals/freetype sources (skia_use_system_freetype2),
  # so the resulting freetype2 static library travels with the artifact.
  # skia_use_system_freetype2 is only declared when FreeType is enabled, so it
  # must not be passed when it is disabled.
  if freetype:
    args += [
      'skia_use_freetype=true',
      'skia_use_system_freetype2=false',
    ]
  else:
    args += ['skia_use_freetype=false']

  if isMacos or isIos or isTvos:
    if isMacos:
        args += ['skia_use_fonthost_mac=true']
    args += ['extra_cflags_cc+=["-frtti"]']
    args += ['skia_use_metal=true']
    if isIos:
      args += ['target_os="ios"']
      if isIosSim:
        args += ['ios_use_simulator=true']
        args += ['extra_cflags+=["-mios-simulator-version-min=12.0"]']
      else:
        args += ['ios_min_target="12.0"']
    else:
      if isTvos:
        args += ['target_os="tvos"']
        # Metal needs tvOS version 14 and SK_BUILD_FOR_TVOS to skip legacy iOS checks
        if isTvosSim:
          args += ['ios_use_simulator=true']
          args += ['extra_cflags+=["-mtvos-simulator-version-min=14", "-DSK_BUILD_FOR_TVOS"]']
        else:
          args += ['extra_cflags+=["-mtvos-version-min=14", "-DSK_BUILD_FOR_TVOS"]'] 
      else:
        if 'arm64' == machine:
          args += ['extra_cflags+=["-stdlib=libc++"]']
        else:
          args += ['extra_cflags+=["-stdlib=libc++", "-mmacosx-version-min=10.13"]']
  elif 'linux' == target:
    if 'arm64' == machine:
        args += [
            'skia_gl_standard="gles"',
            'skia_use_egl=true',
            'extra_cflags_cc+=["-fno-exceptions", "-fno-rtti", "-D_GLIBCXX_USE_CXX11_ABI=0", "-mno-outline-atomics"]',
            'cc="gcc-10"',
            'cxx="g++-10"',
        ]
    else:
        args += [
            'extra_cflags_cc+=["-fno-exceptions", "-fno-rtti","-D_GLIBCXX_USE_CXX11_ABI=0"]',
            'cc="gcc-10"',
            'cxx="g++-10"',
        ]
  elif 'windows' == target:
    args += [
      'skia_use_direct3d=true',
      'extra_cflags+=["-DSK_FONT_HOST_USE_SYSTEM_SETTINGS"]',
    ]
    if 'windows' == host:
      clang_path = shutil.which('clang-cl.exe')
      if not clang_path:
        raise Exception("Please install LLVM from https://releases.llvm.org/, and make sure that clang-cl.exe is available in PATH")
      args += [
        'clang_win="' + os.path.dirname(os.path.dirname(clang_path)) + '"',
        'is_trivial_abi=false',
      ]
  elif 'android' == target:
    args += [
      'ndk="'+ ndk + '"'
    ]
  elif 'wasm' == target:
    # brew install emscripten binaryen llvm nodejs
    # echo "BINARYEN_ROOT = '/usr/local'" >> ~/.emscripten
    # echo "LLVM_ROOT = '/opt/homebrew/opt/llvm/bin'" >> ~/.emscripten
    # echo "NODE_JS = '/opt/homebrew/bin/node'" >> ~/.emscripten

    # see skia/modules/canvaskit/compile.sh for reference:
    args += [
        'skia_use_dng_sdk=false',
        'skia_use_libjpeg_turbo_decode=true',
        'skia_use_libjpeg_turbo_encode=true',
        'skia_use_libpng_decode=true',
        'skia_use_libpng_encode=true',
        'skia_use_libwebp_decode=true',
        'skia_use_libwebp_encode=true',
        'skia_use_wuffs=true',
        'skia_use_lua=false',
        'skia_use_webgl=true',
        'skia_use_piex=false',
        'skia_use_system_libpng=false',
        'skia_use_system_libjpeg_turbo=false',
        'skia_use_system_libwebp=false',
        'skia_enable_tools=false',
        'skia_enable_fontmgr_custom_directory=false',
        'skia_enable_fontmgr_custom_embedded=true',
        'skia_enable_fontmgr_custom_empty=true',
        'skia_use_webgl=true',
        'skia_gl_standard="webgl"',
        'skia_use_gl=true',
        'skia_enable_gpu=true',
        'skia_enable_svg=true', # other targets have this set in skia.gni
        'skia_use_expat=true',   # other targets have this set in skia.gni
        'extra_cflags+=["-DSK_SUPPORT_GPU=1", "-DSK_GL", "-DSK_DISABLE_LEGACY_SHADERCONTEXT", "-sSUPPORT_LONGJMP=wasm"]'
    ]

  # Unhide path edit methods for compatible migration
  args += [
    'extra_cflags+=["-USK_HIDE_PATH_EDIT_METHODS"]',
    'extra_cflags_cc+=["-USK_HIDE_PATH_EDIT_METHODS"]',
  ]

  return args

def main():
  os.chdir(os.path.join(os.path.dirname(__file__), os.pardir, 'skia'))

  build_type = common.build_type()
  machine = common.machine()
  host = common.host()
  host_machine = common.host_machine()
  target = common.target()
  ndk = common.ndk()
  freetype = common.freetype()

  args = gn_args(build_type, machine, target, host, host_machine, ndk, freetype)

  ninja = ninja_path(host, host_machine)
  if not os.path.exists(ninja):
    raise Exception('Can not find "' + ninja + '", run script/checkout.py first')

  out = os.path.join('out', build_type + '-' + target + '-' + machine)
  gn = 'gn.exe' if 'windows' == host else 'gn'
  print([os.path.join('bin', gn), 'gen', out, '--args=' + ' '.join(args)])
  subprocess.check_call([os.path.join('bin', gn), 'gen', out, '--args=' + ' '.join(args)])
  subprocess.check_call([ninja, '-C', out, 'skia', 'modules'])

  return 0

if __name__ == '__main__':
  sys.exit(main())
