#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2010 Modelon AB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from assimulo.solvers import CVode
from assimulo.problem import Explicit_Problem

def run_example(with_plots=True):
    r"""
    This is the same example from the Sundials package (cvsRoberts_FSA_dns.c)
    Its purpose is to demonstrate the use of parameters in the differential equation.

    This simple example problem for CVode, due to Robertson
    see http://www.dm.uniba.it/~testset/problems/rober.php, 
    is from chemical kinetics, and consists of the system:
    
    .. math:: 
    
       \dot y_1 &= -p_1 y_1 + p_2 y_2 y_3 \\
       \dot y_2 &= p_1 y_1 - p_2 y_2 y_3 - p_3 y_2^2 \\
       \dot y_3 &= p_3  y_ 2^2
       
    
    on return:
    
       - :dfn:`exp_mod`    problem instance
    
       - :dfn:`exp_sim`    solver instance
    
    """
    
    def f(t, y, p):
        
        yd_0 = -p[0]*y[0]+p[1]*y[1]*y[2] 
        yd_1 = p[0]*y[0]-p[1]*y[1]*y[2]-p[2]*y[1]**2 
        yd_2 = p[2]*y[1]**2
        
        return np.array([yd_0,yd_1,yd_2])
    
    #The initial conditions
    y0 = [1.0,0.0,0.0]          #Initial conditions for y
    
    #Create an Assimulo explicit problem
    exp_mod = Explicit_Problem(f,y0, name='Robertson Chemical Kinetics Example')
    
    #Sets the options to the problem
    exp_mod.p0 = [0.040, 1.0e4, 3.0e7]  #Initial conditions for parameters
    exp_mod.pbar = [0.040, 1.0e4, 3.0e7]

    #Create an Assimulo explicit solver (CVode)
    exp_sim = CVode(exp_mod)
    
    #Sets the solver parameters
    exp_sim.iter = 'Newton'
    exp_sim.discr = 'BDF'
    exp_sim.rtol = 1.e-4
    exp_sim.atol = np.array([1.0e-8, 1.0e-14, 1.0e-6])
    exp_sim.sensmethod = 'SIMULTANEOUS' #Defines the sensitivity method used
    exp_sim.suppress_sens = False       #Dont suppress the sensitivity variables in the error test.
    exp_sim.report_continuously = True

    #Simulate
    t, y = exp_sim.simulate(4,400) #Simulate 4 seconds with 400 communication points
    
    #Plot
    if with_plots:
        import pylab as pl
        pl.plot(t, y)
        pl.title(exp_mod.name)
        pl.xlabel('Time')
        pl.ylabel('State')
        pl.show()  
    
    #Basic test
    assert abs(y[-1][0] - 9.05518032e-01) < 1e-4
    assert abs(y[-1][1] - 2.24046805e-05) < 1e-4
    assert abs(y[-1][2] - 9.44595637e-02) < 1e-4
    # Values taken from the example in Sundials
    assert abs(exp_sim.p_sol[0][-1][0] + 1.8761) < 1e-2
    assert abs(exp_sim.p_sol[1][-1][0] - 2.9614e-06) < 1e-8
    assert abs(exp_sim.p_sol[2][-1][0] + 4.9334e-10) < 1e-12
    
    return exp_mod, exp_sim

if __name__=='__main__':
    mod,sim = run_example()
