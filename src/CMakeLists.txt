# Source directory CMakeLists.txt for Assimulo

# Find Cython
find_program(CYTHON_EXECUTABLE cython)
if(NOT CYTHON_EXECUTABLE)
    message(FATAL_ERROR "Cython not found. Please install Cython >= 3.0")
endif()

# Get Cython version
execute_process(
    COMMAND ${CYTHON_EXECUTABLE} --version
    OUTPUT_VARIABLE CYTHON_VERSION_OUTPUT
    ERROR_VARIABLE CYTHON_VERSION_OUTPUT
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
string(REGEX MATCH "([0-9]+\.[0-9]+)" CYTHON_VERSION ${CYTHON_VERSION_OUTPUT})
message(STATUS "Found Cython version: ${CYTHON_VERSION}")

# Function to create Cython extensions
function(add_cython_extension target_name source_file)
    # Get the source file without extension
    get_filename_component(source_name ${source_file} NAME_WE)
    
    # Generate C file from Cython
    set(generated_c_file "${CMAKE_CURRENT_BINARY_DIR}/${source_name}.c")
    
    add_custom_command(
        OUTPUT ${generated_c_file}
        COMMAND ${CYTHON_EXECUTABLE} 
            --3str
            -I ${CMAKE_CURRENT_SOURCE_DIR}
            -I ${CMAKE_CURRENT_SOURCE_DIR}/lib
            -o ${generated_c_file}
            ${CMAKE_CURRENT_SOURCE_DIR}/${source_file}
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${source_file}
        COMMENT "Generating C code from ${source_file}"
    )
    
    # Create Python extension module
    python_add_library(${target_name} MODULE ${generated_c_file} WITH_SOABI)
    
    # Add NumPy include directory
    target_include_directories(${target_name} PRIVATE 
        ${Python_NumPy_INCLUDE_DIRS}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/lib
    )
    
    # Link against Python
    target_link_libraries(${target_name} PRIVATE Python::Module)
    
    # Platform-specific settings
    if(WIN32)
        target_compile_definitions(${target_name} PRIVATE NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION)
    endif()
    
    # Handle additional arguments
    set(extra_sources ${ARGN})
    if(extra_sources)
        target_sources(${target_name} PRIVATE ${extra_sources})
    endif()
endfunction()

# Core Assimulo modules
set(CORE_MODULES
    explicit_ode
    implicit_ode  
    ode
    problem
    special_systems
    support
    algebraic
)

# Build core modules
foreach(module ${CORE_MODULES})
    add_cython_extension(${module} ${module}.pyx)
    
    # Special handling for explicit_ode
    if(module STREQUAL "explicit_ode")
        target_sources(${module} PRIVATE ode_event_locator.c)
    endif()
    
    # Install the module
    install(TARGETS ${module} DESTINATION .)
endforeach()

# Solver modules
add_subdirectory(solvers)

# Fortran extensions (third-party solvers)
if(WITH_FORTRAN AND CMAKE_Fortran_COMPILER)
    add_subdirectory(../thirdparty thirdparty)
endif()

# Install Python files and headers
file(GLOB PYTHON_FILES "*.py")
file(GLOB HEADER_FILES "*.pxd" "lib/*.pxd")

install(FILES ${PYTHON_FILES} DESTINATION .)
install(FILES ${HEADER_FILES} DESTINATION .) 