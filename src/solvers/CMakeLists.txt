# Solver modules CMakeLists.txt

# Basic solver: Euler
add_cython_extension(euler euler.pyx)
install(TARGETS euler DESTINATION solvers)

# SUNDIALS solvers (if available)
if(WITH_SUNDIALS AND SUNDIALS_FOUND)
    message(STATUS "Building SUNDIALS solvers")
    
    # Main SUNDIALS solver (CVode, IDA)
    add_cython_extension(sundials sundials.pyx)
    target_include_directories(sundials PRIVATE ${SUNDIALS_INCLUDE_DIRS})
    target_link_libraries(sundials PRIVATE ${SUNDIALS_LIBRARIES})
    
    # Add compile-time definitions for SUNDIALS configuration
    if(SUNDIALS_VERSION)
        string(REPLACE "." ";" SUNDIALS_VERSION_LIST ${SUNDIALS_VERSION})
        list(GET SUNDIALS_VERSION_LIST 0 SUNDIALS_MAJOR)
        list(GET SUNDIALS_VERSION_LIST 1 SUNDIALS_MINOR)
        list(GET SUNDIALS_VERSION_LIST 2 SUNDIALS_PATCH)
        
        target_compile_definitions(sundials PRIVATE
            SUNDIALS_MAJOR_VERSION=${SUNDIALS_MAJOR}
            SUNDIALS_MINOR_VERSION=${SUNDIALS_MINOR}
            SUNDIALS_PATCH_VERSION=${SUNDIALS_PATCH}
        )
    endif()
    
    if(SUNDIALS_WITH_SUPERLU)
        target_compile_definitions(sundials PRIVATE SUNDIALS_WITH_SUPERLU=1)
    endif()
    
    if(SUNDIALS_INDEX_SIZE)
        target_compile_definitions(sundials PRIVATE SUNDIALS_INDEX_SIZE=${SUNDIALS_INDEX_SIZE})
    endif()
    
    # KINSOL solver
    add_cython_extension(kinsol kinsol.pyx)
    target_include_directories(kinsol PRIVATE ${SUNDIALS_INCLUDE_DIRS})
    target_link_libraries(kinsol PRIVATE ${SUNDIALS_LIBRARIES})
    
    # Apply same definitions to kinsol
    if(SUNDIALS_VERSION)
        target_compile_definitions(kinsol PRIVATE
            SUNDIALS_MAJOR_VERSION=${SUNDIALS_MAJOR}
            SUNDIALS_MINOR_VERSION=${SUNDIALS_MINOR}
            SUNDIALS_PATCH_VERSION=${SUNDIALS_PATCH}
        )
    endif()
    
    if(SUNDIALS_WITH_SUPERLU)
        target_compile_definitions(kinsol PRIVATE SUNDIALS_WITH_SUPERLU=1)
        if(WITH_SUPERLU AND SUPERLU_FOUND)
            target_include_directories(sundials PRIVATE ${SUPERLU_INCLUDE_DIRS})
            target_include_directories(kinsol PRIVATE ${SUPERLU_INCLUDE_DIRS})
            target_link_libraries(sundials PRIVATE ${SUPERLU_LIBRARIES})
            target_link_libraries(kinsol PRIVATE ${SUPERLU_LIBRARIES})
        endif()
    endif()
    
    install(TARGETS sundials kinsol DESTINATION solvers)
    
else()
    message(STATUS "SUNDIALS not found - skipping SUNDIALS solvers")
endif()

# Install Python solver files
file(GLOB SOLVER_PYTHON_FILES "*.py")
install(FILES ${SOLVER_PYTHON_FILES} DESTINATION solvers) 