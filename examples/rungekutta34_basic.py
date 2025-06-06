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
from assimulo.solvers import RungeKutta34
from assimulo.problem import Explicit_Problem

def run_example(with_plots=True):
    r"""
    Demonstration of the use of the use of Runge-Kutta 34 by solving the
    linear test equation :math:`\dot y = - y`
    
    on return:
    
       - :dfn:`exp_mod`    problem instance
    
       - :dfn:`exp_sim`    solver instance
       
    """
        
    #Defines the rhs
    def f(t,y):
        ydot = -y[0]
        return np.array([ydot])

    #Define an Assimulo problem
    exp_mod = Explicit_Problem(f, 4.0,
              name = r'RK34 Example: $\dot y = - y$')
    
    exp_sim = RungeKutta34(exp_mod) #Create a RungeKutta34 solver
    exp_sim.inith = 0.1 #Sets the initial step, default = 0.01
    
    #Simulate
    t, y = exp_sim.simulate(5) #Simulate 5 seconds
    
    #Basic test
    assert abs(y[-1][0] - 0.02695199) < 1e-5
    
    #Plot
    if with_plots:
        import pylab as pl
        pl.plot(t, y)
        pl.title(exp_mod.name)
        pl.ylabel('y')
        pl.xlabel('Time')
        pl.show()
    
    return exp_mod, exp_sim  

if __name__=='__main__':
    mod,sim = run_example()
