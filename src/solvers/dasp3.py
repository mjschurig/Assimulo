#!/usr/bin/env python 
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Modelon AB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import numpy as np

from assimulo.problem import SingPerturbed_Problem
from assimulo.exception import Explicit_ODE_Exception, DASP3_Exception
from assimulo.ode import NORMAL, ID_PY_COMPLETE

from assimulo.explicit_ode import Explicit_ODE

try:
    from assimulo.lib import dasp3dp
except ImportError:
    pass

class DASP3ODE(Explicit_ODE):
    """
    DASP3 Solver by Gustaf Söderlind (1980-10-22). Originally published
    in,::
    
        DASP3 - A Program for the Numerical Integration of Partitioned: 
        Stiff Ode:s and Differential-Algebraic Systems.
        
        By, Gustaf Söderlind, Department of Numerical Analysis, and 
        Computing Science, The Royal Institute of Technology, 1980. 
        Stockholm, Sweden.

    DASP3 solves system on the form,
    
    .. math::
      
      \\frac{\\mathrm{d}y}{\\mathrm{d}t} &=  f(t,y,z) \\;\\;\\;  \\text{(N equations)} \\\\
      \\varepsilon\\frac{\\mathrm{d}z}{\\mathrm{d}t} &= G(t,y,z)\\;\\;\\;  \\text{(M equations)}       
    
    If is assumed that the first system is non-stiff and that
    the stiffness of the second system is due to the parameter
    epsilon, possibly a diagonal matrix.
    """
    
    def __init__(self, problem):
        """
        Initiates the solver.
        
            Parameters::
            
                problem     
                            - The problem to be solved. Should be an instance
                              of the 'Explicit_Problem' class.
        """
        Explicit_ODE.__init__(self, problem) #Calls the base class
        if not isinstance(problem, SingPerturbed_Problem):
            raise Explicit_ODE_Exception('The problem needs to be a subclass of a SingPerturbed_Problem.')
        self.n=self.problem.n
        self.m=self.problem.m
        
        # Set initial values
        self.wsy=np.empty((10*self.n,))
        self.wsy[:self.n]=self.problem.yy0
        self.wsz=np.empty((max(9*self.m,1),))  # array must be at least 1 element long
        self.wsz[:self.m]=self.problem.zz0

        # - Default values
        self.options["atol"]     = 1.0e-6*np.ones(self.problem_info["dim"]) #Absolute tolerance
        self.options["rtol"]     = 1.0e-6 #Relative tolerance
        
        self.statistics.add_key("nyder", "Number of slow function evaluations (Y)")
        self.statistics.add_key("nzder", "Number of fast function evaluations (Z)")

    def initialize(self):
        #Reset statistics
        self.statistics.reset()
            
        self._tlist = []
        self._ylist = []
        
    def _solout(self, t, wsy, wsz, n, m, jstop):
        """
        This method is called after every successful step taken by DASP3
        """        
        self._tlist.append(t)
        self._ylist.append(np.hstack((wsy[:n],wsz[:m])))
        
        if self._opts["report_continuously"]:
            initialize_flag = self.report_solution(t, np.hstack((wsy[:n],wsz[:m])), self._opts)
            if initialize_flag: 
                jstop = -1
        else:
            self._tlist.append(t)
            self._ylist.append(np.hstack((wsy[:n],wsz[:m])))
        
        return jstop
            
    def integrate(self, t, y, tf, opts):
        atol=self.options["atol"]
        tol=self.options["rtol"]
        absrel=atol/tol
        
        m = self.problem.m
        n = self.problem.n
        
        a = np.empty((m,m))
        w = np.empty((m,m))
        slu= np.empty((2*m,))
        ips= np.empty((m,),'int32')
        ind = np.empty((2*m,),'int32')
        eq= np.empty((m,),'bool')
        wght=np.ones((m+n,))
        
        #Store the opts
        self._opts = opts
        
        t,lflag=dasp3dp.dasp3(self.problem.rhs1,self.problem.rhs2,self._solout,t,tf,self.wsy,self.wsz,n,m,tol,
                                     absrel,wght,self.problem.eps,a,w,slu,ips,eq,ind)

        #Checking return
        if lflag ==  0:
            flag = ID_PY_COMPLETE
        else:
            raise Exception("DASP3 failed with flag %d"%lflag)
        
        #Retrieving statistics
        self.statistics["nsteps"]      += dasp3dp.COUNTS.NSTEP
        self.statistics["nyder"]        += dasp3dp.COUNTS.NYDER
        self.statistics["nzder"]        += dasp3dp.COUNTS.NZDER
        self.statistics["nerrfails"]     +=  dasp3dp.COUNTS.NREJ
        self.statistics["nlus"]         += 0
        
        return flag, self._tlist, self._ylist
    
    def print_statistics(self, verbose=NORMAL):
        """
        Prints the run-time statistics for the problem.
        """
        log_message_verbose = lambda msg: self.log_message(msg, verbose)
        log_message_verbose('Final Run Statistics: %s \n' % self.problem.name)
        log_message_verbose('\nSolver options:\n')
        log_message_verbose(' Solver                  : DASP3 ')
        log_message_verbose(' Tolerances (absolute)   : ' + str(self._compact_tol(self.options["atol"])))
        log_message_verbose(' Tolerances (relative)   : ' + str(self.options["rtol"]))
        log_message_verbose('')
    
    def _set_atol(self,atol):
        
        self.options["atol"] = np.array(atol,dtype=float) if len(np.array(atol,dtype=float).shape)>0 else np.array([atol],dtype=float)
    
        if len(self.options["atol"]) == 1:
            self.options["atol"] = self.options["atol"]*np.ones(self.problem_info["dim"])
        elif len(self.options["atol"]) != self.problem_info["dim"]:
            raise DASP3_Exception("atol must be of length one or same as the dimension of the problem.")

    def _get_atol(self):
        """
        Defines the absolute tolerance(s) that is to be used by the solver.
        Can be set differently for each variable.
        
            Parameters::
            
                atol    
                        - Default '1.0e-6'.
                
                        - Should be a positive float or a numpy vector
                          of floats.
                        
                            Example:
                                atol = [1.0e-4, 1.0e-6]
        """
        return self.options["atol"]
    
    atol=property(_get_atol,_set_atol)
    
    def _set_rtol(self,rtol):
        try:
            self.options["rtol"] = float(rtol)
        except (ValueError, TypeError):
            raise DASP3_Exception('Relative tolerance must be a (scalar) float.')
        if self.options["rtol"] <= 0.0:
            raise DASP3_Exception('Relative tolerance must be a positive (scalar) float.')
    
    def _get_rtol(self):
        """
        Defines the relative tolerance that is to be used by the solver.
        
            Parameters::
            
                rtol    
                        - Default '1.0e-6'.
                
                        - Should be a positive float.
                        
                            Example:
                                rtol = 1.0e-4
        """
        return self.options["rtol"]
        
    rtol=property(_get_rtol,_set_rtol)
