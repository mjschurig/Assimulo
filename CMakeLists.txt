cmake_minimum_required(VERSION 3.15)
project(assimulo LANGUAGES C CXX Fortran)

# Set C and C++ standards
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 14)

# Find Python and NumPy
find_package(Python COMPONENTS Interpreter Development.Module NumPy REQUIRED)

# Enable position independent code for shared libraries
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Set up installation paths
if(SKBUILD)
    set(CMAKE_INSTALL_PREFIX ${SKBUILD_PLATLIB_DIR}/assimulo)
endif()

# Configuration options
option(WITH_OPENMP "Enable OpenMP support" OFF)
option(WITH_SUNDIALS "Enable SUNDIALS solvers" OFF)
option(WITH_SUPERLU "Enable SuperLU support" OFF)
option(WITH_MKL "Enable Intel MKL support" OFF)
option(WITH_FORTRAN "Enable Fortran solvers" ON)

# Find optional dependencies
if(WITH_OPENMP)
    find_package(OpenMP)
endif()

# Find BLAS and LAPACK for Fortran solvers
if(WITH_FORTRAN)
    find_package(BLAS)
    find_package(LAPACK)
endif()

# Custom module path for find scripts
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Find optional external libraries
if(WITH_SUNDIALS)
    find_package(SUNDIALS)
endif()

if(WITH_SUPERLU)
    find_package(SuperLU)
endif()

if(WITH_MKL)
    find_package(MKL)
endif()

# Compiler-specific settings
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fno-strict-aliasing")
    if(NOT WIN32)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
    endif()
endif()

if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -std=legacy -fPIC")
endif()

# OpenMP configuration
if(WITH_OPENMP AND OpenMP_FOUND)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} ${OpenMP_Fortran_FLAGS}")
    list(APPEND EXTRA_LIBRARIES ${OpenMP_C_LIBRARIES})
endif()

# Platform-specific settings
if(APPLE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wno-error=return-type")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-error=return-type")
endif()

# Debug/Release configuration
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_definitions(DEBUG_BUILD)
    if(NOT MSVC)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")
    endif()
else()
    if(MSVC)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /O2")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /O2")
    else()
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O2")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")
    endif()
endif()

# Include directories
include_directories(${Python_NumPy_INCLUDE_DIRS})

# Status reporting
message(STATUS "Assimulo configuration:")
message(STATUS "  Python: ${Python_VERSION}")
message(STATUS "  NumPy: ${Python_NumPy_VERSION}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  OpenMP: ${WITH_OPENMP}")
message(STATUS "  SUNDIALS: ${WITH_SUNDIALS}")
message(STATUS "  SuperLU: ${WITH_SUPERLU}")
message(STATUS "  MKL: ${WITH_MKL}")
message(STATUS "  Fortran solvers: ${WITH_FORTRAN}")

# Add subdirectories for different components
add_subdirectory(src) 