# The Flutter tooling requires that developers have CMake 3.10 or later
# installed. You should not increase this version, as doing so will cause
# the plugin to fail to compile for some customers of the plugin.
cmake_minimum_required(VERSION 3.10)

project(sweph_library VERSION 2.10.03 LANGUAGES C)

add_library(sweph SHARED
  "sweph/src/swecl.c"
  "sweph/src/swedate.c"
  "sweph/src/swehel.c"
  "sweph/src/swehouse.c"
  "sweph/src/swejpl.c"
  "sweph/src/swemmoon.c"
  "sweph/src/swemplan.c"
  "sweph/src/sweph.c"
  "sweph/src/swephlib.c"
)

target_include_directories(sweph PRIVATE "sweph/src/")

set_target_properties(sweph PROPERTIES
  PUBLIC_HEADER swephexp.h
  OUTPUT_NAME "sweph"
)

add_definitions(-D_CRT_SECURE_NO_WARNINGS)
IF (WIN32)
  add_definitions(-DMAKE_DLL)
ENDIF()

target_compile_definitions(sweph PUBLIC DART_SHARED_LIB)
