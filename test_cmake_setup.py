#!/usr/bin/env python3
"""
Test script for Assimulo CMake setup validation
This script checks if the CMake build system can be tested
"""
import sys
import subprocess
import os
from pathlib import Path

def test_python_environment():
    """Test Python environment and dependencies"""
    print("=== Python Environment Test ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Test required packages
    required_packages = [
        'numpy', 'scipy', 'matplotlib', 'cython'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            print(f"❌ {package} missing")
            missing_packages.append(package)
    
    # Test optional packages for build system
    optional_packages = {
        'scikit_build_core': 'scikit-build-core',
        'cmake': 'cmake',
    }
    
    for module, package in optional_packages.items():
        try:
            __import__(module)
            print(f"✅ {package} available")
        except ImportError:
            print(f"⚠️  {package} missing (optional for modern build)")
    
    return len(missing_packages) == 0

def test_cmake_availability():
    """Test CMake availability"""
    print("\n=== CMake Test ===")
    try:
        result = subprocess.run(['cmake', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ CMake available: {result.stdout.strip().split()[2]}")
            return True
        else:
            print("❌ CMake not working")
            return False
    except FileNotFoundError:
        print("❌ CMake not found")
        return False

def test_fortran_compiler():
    """Test Fortran compiler availability"""
    print("\n=== Fortran Compiler Test ===")
    compilers = ['gfortran', 'ifort', 'flang']
    
    for compiler in compilers:
        try:
            result = subprocess.run([compiler, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {compiler} available")
                return True
        except FileNotFoundError:
            continue
    
    print("❌ No Fortran compiler found")
    print("   For Windows: Install MinGW-w64 or Intel Fortran")
    print("   For Linux: sudo apt install gfortran")
    print("   For macOS: brew install gcc")
    return False

def test_cmake_files():
    """Test CMake configuration files"""
    print("\n=== CMake Configuration Test ===")
    
    required_files = [
        'CMakeLists.txt',
        'pyproject.toml',
        'src/CMakeLists.txt',
        'src/solvers/CMakeLists.txt',
        'thirdparty/CMakeLists.txt',
        'cmake/FindSUNDIALS.cmake'
    ]
    
    all_present = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_present = False
    
    return all_present

def test_source_structure():
    """Test source code structure for migration"""
    print("\n=== Source Structure Test ===")
    
    # Check for Cython sources
    cython_files = list(Path('src').glob('*.pyx'))
    print(f"✅ Found {len(cython_files)} Cython files")
    
    # Check for Fortran sources
    fortran_files = list(Path('thirdparty').glob('**/*.f*'))
    print(f"✅ Found {len(fortran_files)} Fortran files")
    
    # Check for f2py interface files
    pyf_files = list(Path('thirdparty').glob('**/*.pyf'))
    print(f"⚠️  Found {len(pyf_files)} .pyf files (need migration)")
    
    return True

def test_build_attempt():
    """Test if we can attempt a build"""
    print("\n=== Build Test (Dry Run) ===")
    
    # Check if pyproject.toml is valid
    try:
        import tomllib
        with open('pyproject.toml', 'rb') as f:
            config = tomllib.load(f)
        print("✅ pyproject.toml is valid TOML")
        
        if 'build-system' in config:
            backend = config['build-system'].get('build-backend', 'unknown')
            print(f"✅ Build backend configured: {backend}")
        
        return True
    except Exception as e:
        print(f"❌ pyproject.toml issue: {e}")
        return False

def main():
    """Main test function"""
    print("Assimulo CMake Migration - Setup Validation")
    print("=" * 50)
    
    tests = [
        ("Python Environment", test_python_environment),
        ("CMake Availability", test_cmake_availability),
        ("Fortran Compiler", test_fortran_compiler),
        ("CMake Files", test_cmake_files),
        ("Source Structure", test_source_structure),
        ("Build Configuration", test_build_attempt),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 Ready for CMake build!")
        print("Next steps:")
        print("1. Install missing optional dependencies")
        print("2. Try: pip install -e . (with scikit-build-core)")
        print("3. Or: python setup_setuptools.py install (partial build)")
    else:
        print("\n⚠️  Setup needs attention before building")
        print("Please resolve failing tests before proceeding")
    
    return passed == len(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 