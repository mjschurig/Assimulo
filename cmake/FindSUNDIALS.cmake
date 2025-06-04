# FindSUNDIALS.cmake
# Find SUNDIALS library for Assimulo
#
# This module defines:
#  SUNDIALS_FOUND - True if SUNDIALS is found
#  SUNDIALS_INCLUDE_DIRS - Include directories for SUNDIALS
#  SUNDIALS_LIBRARIES - Libraries to link against
#  SUNDIALS_VERSION - Version of SUNDIALS found
#
# Environment variables:
#  SUNDIALS_ROOT - Root directory of SUNDIALS installation

# Find include directory
find_path(SUNDIALS_INCLUDE_DIR
    NAMES cvodes/cvodes.h
    HINTS
        ${SUNDIALS_ROOT}
        $ENV{SUNDIALS_ROOT}
        ${SUNDIALS_ROOT}/include
        $ENV{SUNDIALS_ROOT}/include
    PATHS
        /usr/local/include
        /usr/include
        /opt/local/include
        /sw/include
        C:/sundials/include
    PATH_SUFFIXES
        sundials
)

# Find library directory
find_path(SUNDIALS_LIBRARY_DIR
    NAMES libsundials_cvodes.a libsundials_cvodes.so sundials_cvodes.lib
    HINTS
        ${SUNDIALS_ROOT}
        $ENV{SUNDIALS_ROOT}
        ${SUNDIALS_ROOT}/lib
        $ENV{SUNDIALS_ROOT}/lib
    PATHS
        /usr/local/lib
        /usr/lib
        /opt/local/lib
        /sw/lib
        C:/sundials/lib
)

# Find individual libraries
set(SUNDIALS_LIBRARY_NAMES
    sundials_cvodes
    sundials_idas
    sundials_kinsol
    sundials_nvecserial
)

# For SUNDIALS >= 3.0
list(APPEND SUNDIALS_LIBRARY_NAMES
    sundials_sunlinsoldense
    sundials_sunlinsolspgmr
    sundials_sunmatrixdense
    sundials_sunmatrixsparse
)

# For SUNDIALS >= 7.0
list(APPEND SUNDIALS_LIBRARY_NAMES
    sundials_core
)

# For SUNDIALS with SuperLU support
list(APPEND SUNDIALS_LIBRARY_NAMES
    sundials_sunlinsolsuperlumt
)

set(SUNDIALS_LIBRARIES)
foreach(lib_name ${SUNDIALS_LIBRARY_NAMES})
    find_library(SUNDIALS_${lib_name}_LIBRARY
        NAMES ${lib_name}
        HINTS ${SUNDIALS_LIBRARY_DIR}
        NO_DEFAULT_PATH
    )
    if(SUNDIALS_${lib_name}_LIBRARY)
        list(APPEND SUNDIALS_LIBRARIES ${SUNDIALS_${lib_name}_LIBRARY})
    endif()
endforeach()

# Try to determine version
if(SUNDIALS_INCLUDE_DIR)
    file(READ "${SUNDIALS_INCLUDE_DIR}/sundials/sundials_config.h" SUNDIALS_CONFIG_H)
    
    # Look for version string
    string(REGEX MATCH "#define SUNDIALS_PACKAGE_VERSION \"([0-9]+\.[0-9]+\.[0-9]+)\"" 
           SUNDIALS_VERSION_MATCH "${SUNDIALS_CONFIG_H}")
    if(SUNDIALS_VERSION_MATCH)
        set(SUNDIALS_VERSION ${CMAKE_MATCH_1})
    else()
        # Try alternative version format
        string(REGEX MATCH "#define SUNDIALS_VERSION \"([0-9]+\.[0-9]+\.[0-9]+)\"" 
               SUNDIALS_VERSION_MATCH "${SUNDIALS_CONFIG_H}")
        if(SUNDIALS_VERSION_MATCH)
            set(SUNDIALS_VERSION ${CMAKE_MATCH_1})
        endif()
    endif()
    
    # Check for SuperLU support
    string(FIND "${SUNDIALS_CONFIG_H}" "SUNDIALS_SUPERLUMT" SUNDIALS_HAS_SUPERLU)
    if(NOT SUNDIALS_HAS_SUPERLU EQUAL -1)
        set(SUNDIALS_WITH_SUPERLU TRUE)
    else()
        set(SUNDIALS_WITH_SUPERLU FALSE)
    endif()
    
    # Check for vector size configuration
    string(FIND "${SUNDIALS_CONFIG_H}" "SUNDIALS_INT32_T" SUNDIALS_HAS_INT32)
    string(FIND "${SUNDIALS_CONFIG_H}" "SUNDIALS_INT64_T" SUNDIALS_HAS_INT64)
    if(NOT SUNDIALS_HAS_INT32 EQUAL -1)
        set(SUNDIALS_INDEX_SIZE 32)
    elseif(NOT SUNDIALS_HAS_INT64 EQUAL -1)
        set(SUNDIALS_INDEX_SIZE 64)
    endif()
endif()

# Set up variables
set(SUNDIALS_INCLUDE_DIRS ${SUNDIALS_INCLUDE_DIR})

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(SUNDIALS
    REQUIRED_VARS SUNDIALS_INCLUDE_DIR SUNDIALS_LIBRARIES
    VERSION_VAR SUNDIALS_VERSION
)

if(SUNDIALS_FOUND)
    message(STATUS "Found SUNDIALS version: ${SUNDIALS_VERSION}")
    if(SUNDIALS_WITH_SUPERLU)
        message(STATUS "SUNDIALS compiled with SuperLU support")
    endif()
    if(SUNDIALS_INDEX_SIZE)
        message(STATUS "SUNDIALS index size: ${SUNDIALS_INDEX_SIZE} bit")
    endif()
endif()

mark_as_advanced(
    SUNDIALS_INCLUDE_DIR
    SUNDIALS_LIBRARY_DIR
    SUNDIALS_VERSION
    SUNDIALS_WITH_SUPERLU
    SUNDIALS_INDEX_SIZE
) 