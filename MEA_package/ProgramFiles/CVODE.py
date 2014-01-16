################################################################################
# Function to call CVODE solver (first need to create and compile C file from 
# template file using create_C.py)
#
################################################################################

from array import array
from math import *
from ctypes import *
from numpy import *
import time
import matplotlib.pylab as plt
from create_cfile import create_c

######################################################################
# Input:
# library is compiled C file (file.so.1.0 format)
"""
# outfile (name of file to write trajectory data to if selected)
"""
# t = list of timepoints
# t0_sp = list of starting values for each species (moment)
# param = list of parameter values to solve with
######################################################################

def CVODE(library, t, t0_sp, param):
    
    starttime = t[0]
    endtime = t[-1]
    ntimepoints = len(t)
    libmylib = CDLL(library) 
    nspecies = len(t0_sp)     #no of equations to be solved 
    npar = len(param)        #no of parameters (rate constants)
    
    
    """        # use to print all solutions to outfile if wanted
    def print_results(result, outfile):
        out = open(outfile,'w')
        print >>out, 0, 0, 0,
        for i in range(ntimepoints):
            print >>out, timepoints[i],
        print >>out, ""
    # loop over threads
        for i in range(nsim):
        # loop over species
            for l in range(nspecies):               
                print >>out, i,0,l,
                for k in range(ntimepoints):
                    print >>out, result[i,k,l],
                print >>out, ""
        out.close()
    """

    t0=time.time()
    
    nsim=1
    
    # create C type data arrays to pass to CVODE

    parameters=zeros([nsim, npar])
    init_sp = zeros([nsim,nspecies])
    for i in range(nsim):
        parameters[i,:] = param
        init_sp[i,:] = t0_sp
   
    arr_type=npar*nsim*c_double
    param_c=arr_type()
    ind=0
    for i in range (nsim):
        for j in range(npar):
            param_c[ind]=parameters[i,j]
            ind+=1

    arr_type2=nspecies*nsim*c_double
    init_sp_c=arr_type2()
    ind=0
    for i in range (nsim):
        for j in range(nspecies):
            init_sp_c[ind]=init_sp[i,j]
            ind+=1
    arr_type_mat=nsim*nspecies*ntimepoints*c_double
    res_c=arr_type_mat()
    for i in range(nsim*ntimepoints*nspecies):
        res_c[i]=0.0

    arr_type_t = ntimepoints*c_double
    time_c = arr_type_t()
    for i in range(ntimepoints):
        time_c[i] = t[i]

    # call CVODE and format results

    libmylib.ftest(byref(param_c),nsim,byref(init_sp_c), byref(res_c), byref(time_c))

   
    results=zeros([nsim, ntimepoints, nspecies])
    ind=0
    for i in range(nsim):
        for t_ in range(ntimepoints):
            for sp in range(nspecies):
                results[i,t_,sp]=res_c[ind]
                ind+=1
    
    # soln is array with a row for each timepoint, giving values for each species
 
    soln = zeros([ntimepoints,nspecies])
    for k in range(ntimepoints):
        for l in range(nspecies):
            soln[k,l] = results[0,k,l]
    
    #print "final time=", time.time()-t0
    #print_results(results, outfile)
    
    return soln

