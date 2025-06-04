# Third-party Fortran solvers CMakeLists.txt

if(NOT CMAKE_Fortran_COMPILER)
    message(STATUS "No Fortran compiler found - skipping Fortran solvers")
    return()
endif()

message(STATUS "Building Fortran third-party solvers")

# Function to create Fortran extension with Cython wrapper
function(add_fortran_extension target_name fortran_sources cython_wrapper)
    # Compile Fortran sources into object library
    add_library(${target_name}_fortran OBJECT ${fortran_sources})
    
    # Set Fortran compilation flags
    target_compile_options(${target_name}_fortran PRIVATE
        $<$<Fortran_COMPILER_ID:GNU>:-std=legacy -fPIC>
        $<$<Fortran_COMPILER_ID:Intel>:-stand f90 -fPIC>
    )
    
    # Create Cython wrapper extension
    get_filename_component(wrapper_name ${cython_wrapper} NAME_WE)
    set(generated_c_file "${CMAKE_CURRENT_BINARY_DIR}/${wrapper_name}.c")
    
    add_custom_command(
        OUTPUT ${generated_c_file}
        COMMAND ${CYTHON_EXECUTABLE}
            --3str
            -I ${CMAKE_CURRENT_SOURCE_DIR}
            -I ${CMAKE_SOURCE_DIR}/src
            -I ${CMAKE_SOURCE_DIR}/src/lib
            -o ${generated_c_file}
            ${CMAKE_CURRENT_SOURCE_DIR}/${cython_wrapper}
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${cython_wrapper}
        COMMENT "Generating C code from ${cython_wrapper}"
    )
    
    # Create Python extension module
    python_add_library(${target_name} MODULE 
        ${generated_c_file}
        $<TARGET_OBJECTS:${target_name}_fortran>
        WITH_SOABI
    )
    
    # Set up include directories and libraries
    target_include_directories(${target_name} PRIVATE
        ${Python_NumPy_INCLUDE_DIRS}
        ${CMAKE_SOURCE_DIR}/src
        ${CMAKE_SOURCE_DIR}/src/lib
        ${CMAKE_CURRENT_SOURCE_DIR}
    )
    
    target_link_libraries(${target_name} PRIVATE Python::Module)
    
    # Add math library on Unix systems
    if(UNIX AND NOT APPLE)
        target_link_libraries(${target_name} PRIVATE m)
    endif()
    
    # Install the module
    install(TARGETS ${target_name} DESTINATION lib)
endfunction()

# DOPRI5 - Prototype implementation
message(STATUS "Building DOPRI5 (prototype)")
set(DOPRI5_SOURCES hairer/dopri5.f)
set(DOPRI5_WRAPPER hairer/dopri5_wrapper.pyx)

# Create a simple Cython wrapper for DOPRI5 (prototype)
file(WRITE ${CMAKE_CURRENT_SOURCE_DIR}/hairer/dopri5_wrapper.pyx "
# DOPRI5 Cython wrapper - Prototype
# This replaces the f2py interface in dopri5.pyf

import numpy as np
cimport numpy as np
from libc.stdlib cimport malloc, free

# Fortran function declarations
cdef extern void dopri5_(int* n, void* fcn, double* x, double* y, double* xend,
                        double* rtol, double* atol, int* itol, void* solout,
                        int* iout, double* work, int* lwork, int* iwork, 
                        int* liwork, double* rpar, int* ipar, int* idid)

cdef extern double contd5_(int* ii, double* x, double* con, int* icomp, int* nd)

# Callback function pointer types
ctypedef void (*fcn_callback_t)(int* n, double* x, double* y, double* k1, double* rpar, int* ipar)
ctypedef void (*solout_callback_t)(double* naccpt, double* xold, double* x, double* y, int* n,
                                  double* cont, int* icomp, int* nrd, double* rpar, int* ipar, int* irtrn)

# Global callback references
cdef object _fcn_callback = None
cdef object _solout_callback = None

# C callback wrappers
cdef void c_fcn_callback(int* n, double* x, double* y, double* k1, double* rpar, int* ipar) noexcept:
    if _fcn_callback is not None:
        n_val = n[0]
        x_val = x[0]
        y_array = np.asarray(<double[:n_val]>y)
        k1_result = _fcn_callback(x_val, y_array)
        cdef int i
        for i in range(n_val):
            k1[i] = k1_result[i]

cdef void c_solout_callback(double* naccpt, double* xold, double* x, double* y, int* n,
                           double* cont, int* icomp, int* nrd, double* rpar, int* ipar, int* irtrn) noexcept:
    if _solout_callback is not None:
        n_val = n[0]
        y_array = np.asarray(<double[:n_val]>y)
        result = _solout_callback(x[0], y_array)
        irtrn[0] = 0 if result else -1

def dopri5_solve(fcn, double x, np.ndarray[double, ndim=1] y, double xend,
                np.ndarray[double, ndim=1] rtol, np.ndarray[double, ndim=1] atol,
                int itol, solout=None, int iout=0):
    '''
    DOPRI5 ODE solver - Cython wrapper
    
    This replaces the f2py interface with a modern Cython implementation.
    '''
    global _fcn_callback, _solout_callback
    
    cdef int n = len(y)
    cdef int lwork = 8 * n + 21
    cdef int liwork = 21
    cdef int idid
    
    # Allocate work arrays
    cdef double* work = <double*>malloc(lwork * sizeof(double))
    cdef int* iwork = <int*>malloc(liwork * sizeof(int))
    cdef double* rpar = <double*>malloc(sizeof(double))
    cdef int* ipar = <int*>malloc(sizeof(int))
    
    try:
        # Set callbacks
        _fcn_callback = fcn
        _solout_callback = solout
        
        # Initialize work arrays
        for i in range(liwork):
            iwork[i] = 0
        
        # Call Fortran routine
        dopri5_(&n, <void*>c_fcn_callback, &x, &y[0], &xend,
                &rtol[0], &atol[0], &itol, 
                <void*>c_solout_callback if solout else NULL,
                &iout, work, &lwork, iwork, &liwork, rpar, ipar, &idid)
        
        return idid, x
        
    finally:
        free(work)
        free(iwork)
        free(rpar)
        free(ipar)
        _fcn_callback = None
        _solout_callback = None
")

# Build DOPRI5 with the new wrapper
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/hairer/dopri5.f)
    add_fortran_extension(dopri5 "${DOPRI5_SOURCES}" "${DOPRI5_WRAPPER}")
    message(STATUS "DOPRI5 built successfully as prototype")
else()
    message(WARNING "DOPRI5 source file not found - skipping")
endif()

# TODO: Add other Fortran solvers
# add_subdirectory(hairer)    # DOPRI5, RODAS, RADAU5, RADAR5
# add_subdirectory(odepack)   # LSODA, LSODAR, etc.
# add_subdirectory(odassl)    # ODASSL DAE solver
# add_subdirectory(dasp3)     # DASP3 singular perturbation
# add_subdirectory(glimda)    # GLIMDA multistep DAE

message(STATUS "Fortran solvers configuration complete")
message(STATUS "Note: This is a prototype implementation. Additional solvers need migration.") 