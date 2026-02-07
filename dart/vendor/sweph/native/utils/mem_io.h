#ifndef __ASSET_SAVER_H
#define __ASSET_SAVER_H

#include <stddef.h>
#include <stdio.h>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

#ifdef __cplusplus
extern "C" {
#endif

#if defined(MAKE_DLL) || defined(USE_DLL) || defined(_WINDOWS)
#include <windows.h>
extern HANDLE dllhandle; // set by swedllst::DllMain,
                         // defined in sweph.c
                         // used by GetModuleFilename in sweph.c
#endif

#ifdef MAKE_DLL
#if defined(PASCAL) || defined(__stdcall)
#if defined UNDECO_DLL
#define CALL_CONV EMSCRIPTEN_KEEPALIVE __cdecl
#else
#define CALL_CONV EMSCRIPTEN_KEEPALIVE __stdcall
#endif
#else
#define CALL_CONV EMSCRIPTEN_KEEPALIVE
#endif
/* To export symbols in the new DLL model of Win32, Microsoft
   recommends the following approach */
#define EXP32 __declspec(dllexport)
#else
#define CALL_CONV EMSCRIPTEN_KEEPALIVE
#define EXP32
#endif

/* ext_def(x) evaluates to x on Unix */
#define ext_def(x) extern EXP32 x CALL_CONV

ext_def(int) write_file(const char* path, char* contents, size_t len, int forceOverwrite);

#ifdef __cplusplus
}
#endif

#endif // __ASSET_SAVER_H
