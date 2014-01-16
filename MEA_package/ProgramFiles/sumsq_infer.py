#################################################################
# Functions used for parameter inference.  Selected rate constants
# and initial conditions are varied to minimise the cost function.
# Minimization uses the Nelder-Mead simplex algorithm (python fmin).
# The default cost function calculates the distance (sum of squared
# differences) between the sample data moments and moments 
# calculated using MFK at each of the specified timepoints.
#################################################################
import numpy as np
from sympy import Matrix
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.optimize import fmin
from CVODE import CVODE
import re
from math import factorial

################################################################
# Functions 'make_i0' and 'i0_to_test'
#
# Explanation of variables (all but i0 provided by user in input file):
# i0        single list of all variable parameters (kinetic parameters
#           or initial conditions) that need to be inferred
# param     list of starting values for kinetic parameters
# vary      list to identify which values in param to vary during inference
# initcond  list of starting values (i.e. at t0) for moments
# varyic    list to identify which values in initcond to vary
#
# make_i0 creates the list of variables to infer based on the values
# in vary/varyic (0 = fixed, 1 = optimise), i0 is passed to the 
# fmin minimisation function.
# 
# i0_to_test is used within the distance/cost function to create 
# the current kinetic parameter and initial condition vectors to
# be used during that iteration, using the current values in i0
##################################################################

def make_i0(param, vary, initcond, varyic):
    i0 = []
    for i in range(0, len(vary)):
        if vary[i] == 1:
            i0.append(param[i])
    for j in range(0, len(varyic)):
        if varyic[j] ==1:
            i0.append(initcond[j])        
    return i0

def i0_to_test(i0, param, vary, initcond, varyic):
    test_param = param[:]
    test_initcond = initcond[:]
    i0_index = 0
    for i in range(0, len(vary)):
        if vary[i] == 1:
            test_param[i] = i0[i0_index]
            i0_index += 1
    for j in range(0, len(varyic)):
        if varyic[j] ==1:
            test_initcond[j] = i0[i0_index]
            i0_index += 1
            
    return (test_param, test_initcond)

##################################################################
# Function to read sample data from file and return 3 lists:
# t         timepoints
# mu        each entry is a timecourse from the sample data file
# mom_names each entry identifies the moment in mu
#           (given as list of powers that each species is raised
#           to e.g. if 3 species, variance of 2nd species given 
#           by [0,2,0].  NB for parametric likelihoods, use e.g. 
#           [1,0,0] to indicate a timecourse of e.g. number of 
#           molecules of 1st species)
##################################################################

def sample_data(sample):
    data_RE = re.compile('>|\n|#')
    datafile = open(sample)
    mu = []
    mom_names = []
    for l in datafile:
        if not data_RE.match(l):
            l = l.rstrip()
            data = l.split('\t')
            #data[-1] = data[-1].rstrip()
            # get timepoints
            if data[0] == 'time':
                t = [float(data[i])for i in range(1,len(data))]
            # get trajectory and name of moment
            else:
                traj = []
                for j in range(1,len(data)):
                    if data[j].strip() == 'N':
                        traj.append(data[j].strip())
                    else:
                        traj.append(float(data[j]))
                #traj = [float(data[j]) for j in range(1,len(data))]
                mu.append(traj)
                moment_str_list = data[0].split(',')
                moment_int_list = [int(p) for p in moment_str_list]
                mom_names.append(moment_int_list)
    datafile.close()
    return (mu,t, mom_names)



###################################################################
# From list of moments in sample file (mom_names), identify the
# indices of the corresponding moments in the simulated trajectories
# produced by CVODE.  Returns indices as a list (mom_index_list).
# 
# Also returns a list of the moments produced by MFK/CVODE (moments_list)
###################################################################

def mom_indices(mfkoutput, mom_names):
    mfkfile = open(mfkoutput)
    lines = mfkfile.readlines()
    mfkfile.close()

    # Get list of moments from mfkoutput to create labels for output data file
    momlistindex = lines.index('List of moments:\n')
    moments_list = []
    for i in range(momlistindex+1, len(lines)):
        if lines[i].startswith('['):
            moment_str = str(lines[i].strip('\n[]'))
            moment_str_list = moment_str.split(',')
            moment_int_list = [int(p) for p in moment_str_list]
            moments_list.append(moment_int_list)

    # Get indices in CVODE solutions for the moments in sample data
    mom_index_list = [moments_list.index(m) for m in mom_names]
    return (mom_index_list,moments_list)


#####################################################################
# Optimise function, used for parameter inference (minimizes
# the distance/cost funtion using a simplex algorithm)
# Arguments: 
# param, vary      kinetic parameters, and list to indicate which to infer
# initcond,varyic  initial conditions, " "
# limits           constrains allowed values for parameters and initial
#                  conditions (list with entry in form [(lower,upper)] 
#                  parameter/initial condition set in timeparam file)
# sample           name of experimental data file
# cfile            name of C library (specified by --library)
# mfkoutput        name of file produced by MFK (specified by --ODEout)
######################################################################
                
def optimise(param, vary, initcond, varyic,limits, sample, cfile, mfkoutput):

    i0 = make_i0(param, vary, initcond, varyic)        # create initial i0
    
    # Get required information from the MFK or LNA output file 

    mfkfile = open(mfkoutput)
    lines = mfkfile.readlines()
    mfkfile.close()
    simtype = lines[0].rstrip()            # simtype = MFK or LNA
    nSpecies_index = lines.index('Number of variables:\n')
    nspecies = int(lines[nSpecies_index +1])

    # If starting values not specified for all moments, set remainder to 0

    nEquation_index = lines.index('Number of equations:\n')
    nEquations = int(lines[nEquation_index+1].strip())
    if len(initcond) != nEquations:
        initcond += ([0]*(nEquations-len(initcond)))

    ######################################################################
    # Evaluates distance (cost) function for current set of values in i0
    #
    # At each iteration, this function is called by fmin and calculated 
    # using the current values in i0.  Returned value (dist) is minimised
    # by varying i0
    #
    # Distance is the sum of squared differences between the sample data
    # and the corresponding values simulated using either MFK or LNA
    # with the current parameter sets.
    #####################################################################

    def distance(i0, param, vary, initcond, varyic, mu, t, cfile, mom_index_list):   

        # value returned if parameters, means or variances < 0
        max_dist = 1.0e10                

        # creates lists of parameters (test_param and test_initcond) for that iteration

        (test_param, test_initcond) = i0_to_test(i0, param, vary, initcond, varyic)
        test_soln = CVODE(cfile,t,test_initcond,test_param)

        # Check if parameters/initconds are within allowed bounds (if --limit used)
        # and return max_dist if outside these ranges
        
        if limits != None:
            for a in range(0, len(i0)):
                l_limit = limits[a][0]
                u_limit = limits[a][1]
                if l_limit != 'N':
                    if i0[a] < l_limit:
                        return max_dist
                if u_limit != 'N':
                    if i0[a] > u_limit:
                        return max_dist

        # If MFK used, distance summed over all timepoints/moments contained 
        # in sample data file

        if simtype == 'MEA':
            if any(i<0 for i in test_param):   # disallow negative kinetic parameters
                return max_dist

            # calculate number of var/covar terms
            #nVar_Covar = factorial(nspecies+1)/(factorial(2)*factorial(nspecies-2))
            #if any(j<0 for j in test_initcond[0:nspecies+nVar_Covar]):
            if any(j<0 for j in test_initcond[0:nspecies]):
                return max_dist              # disallow negative means/variance/covariance
            
            tmu = [test_soln[:,i] for i in range(0, len(initcond))]
            dist = 0
            for sp in range(0, len(mu)):
                for tp in range(0, len(t)):
                    if mu[sp][tp] == 'N':     # account for missing datapoints ('N' in datafile)
                        dist +=0
                    else:
                        dist += (mu[sp][tp] - tmu[mom_index_list[sp]][tp])**2

        # If LNA used...

        if simtype == 'LNA':
            tmu = [0]*nspecies
            mu_t = [0]*len(t)
            for i in range(0,nspecies):
                mu_i = [0]*len(t)
                for j in range(len(t)):
                    if i == 0:
                        V = Matrix(nspecies,nspecies,lambda k,l:0)
                        for v in range(2*nspecies):
                            V[v] = test_soln[j,v+nspecies]
                        mu_t[j] = np.random.multivariate_normal(test_soln[j,0:nspecies],V)
                    mu_i[j]=mu_t[j][i]
                tmu[i]=mu_i
            dist = 0
            for sp in range(0,len(mu)):
                for tp in range(0,len(t)):
                    dist += (mu[sp][tp] - tmu[sp][tp])**2
        
        # Returns distance (dist), (and saves current i0 and dist to list)
        y_list.append(dist) 
        i0_list.append(i0[0])
        return dist
    
    # callback: function called after each iteration (each iteration will involve several
    # distance function evaluations).  Use this to save data after each iteration if wanted.
    # x is the current i0 returned after that iteration.

    def my_callback(x):        
        it_param.append(x)
        it_no.append(len(it_param))
        #it_dist.append(y_list[-1])
        #print x
        #print y_list[-1]
        
    
    # create lists to collect data at each iteration (use with my_callback if wanted)
    y_list = []
    i0_list = []
    it_no = []
    it_param = []
    it_dist = []

    # read sample data from file to get required information to pass to fmin
    (mu, t, mom_names) = sample_data(sample)
    (mom_index_list,moments_list) = mom_indices(mfkoutput, mom_names)

    # minimise defined distance function, with provided starting parameters
    result = fmin(distance, i0, args=(param, vary,initcond,varyic, mu, t, cfile, mom_index_list), ftol = 0.000001,disp=0, full_output=True,callback=my_callback)

    return (result, mu, t, initcond, mom_index_list, moments_list)



########################################################################
# Writes inference results to output file (default name = inference.txt)
#
# 'restart_results' is a list of lists: [[result, mu, param, initcond]].  There will 
# be an internal list for each optimisation performed (i.e. if several
# random restarts selected using --restart option in main menu, each set
# of results, sorted in order of increasing distance will be present in
# restart_results).  If no restarts used, there will just be one internal
# list as in the example here.
#
# 'result' is the output from python fmin function:
# result = (optimised i0, optimised distance, no. of iterations required,
# no. of function evaluations made, warning flag - 0 if successful,
# 1 or 2 if not)
########################################################################

def infer_results(restart_results, t,vary, initcond_full,varyic, inferfile):
    outfile = open(inferfile, 'w')
    for i in range(len(restart_results)):
        outfile.write('Starting parameters:\t'+str(restart_results[i][2])+'\n')
        (opt_param, opt_initconds) = i0_to_test(list(restart_results[i][0][0]), restart_results[i][2], vary, initcond_full,varyic)
        outfile.write('Optimised parameters:\t'+str(opt_param)+'\n')
        outfile.write('Starting initial conditions:\t'+str(restart_results[i][3])+'\n')
        outfile.write('Optimised initial conditions:\t'+str(opt_initconds)+'\n')
        if restart_results[i][0][4] == 0: 
            outfile.write('Optimisation successful:\n')
            outfile.write('\tNumber of iterations: '+str(restart_results[i][0][2])+'\n')
            outfile.write('\tNumber of function evaluations: '+str(restart_results[i][0][3])+'\n')
            outfile.write('\tDistance at minimum: '+str(restart_results[i][0][1])+'\n\n')
        if restart_results[i][0][4] != 0:
            outfile.write('Optimisation terminated: maximum number of iterations or function evaluations exceeded.\n')
            outfile.write('\tNumber of iterations: '+str(restart_results[i][0][2])+'\n')
            outfile.write('\tNumber of function evaluations: '+str(restart_results[i][0][3])+'\n')
            outfile.write('\tDistance at minimum: '+str(restart_results[i][0][1])+'\n\n')


###############################################################################
# Plots graph of data vs inferred trajectories (max of 9 subplots created)
#
# Moment trajectories calculated using initial parameters (green line) and
# optimised parameters (red line), with the experimental data as black circles
###############################################################################

def graph(opt_results, t,lib, initcond_full, vary,varyic, mfkoutput, plottitle, mom_index_list,moments_list):
   
    (opt_param,opt_initcond) = i0_to_test(list(opt_results[0][0]), opt_results[2], vary,initcond_full,varyic)
    mu = opt_results[1]

    # get trajectories for optimised parameters
    opt_soln = CVODE(lib,t,opt_initcond,opt_param)
    opt_mu = [opt_soln[:,i] for i in range(0, len(initcond_full))]
   
    # get trajectories for starting parameters
    start_soln = CVODE(lib,t,opt_results[3],opt_results[2])
    start_mu = [start_soln[:,i] for i in range(0, len(initcond_full))]
    
    # Plot figure (starting vs optimised trajectories, plus experimental data)
    fig = plt.figure()
    plot_list = []
    
    # Allow for missing timepoints in experimental data
    def check_partial_data(times, traj):
        t_list = []
        traj_list = []
        for a in range(len(traj)):
            if traj[a] != 'N':
                t_list.append(times[a])
                traj_list.append(traj[a])
        return(t_list,traj_list)

    for i in mom_index_list:
        new_plot = False
        if i not in plot_list:
            plot_list.append(i)
            new_plot = True

        if len(plot_list)<10:
            j = plot_list.index(i)
            ax = plt.subplot(4,3,j+1)
            (t_list,traj_list) = check_partial_data(t, mu[i])

            # if no plot exists for that moment create subplot, else add to existing subplot 
            if new_plot == True:
                ax.plot(t_list, traj_list, color = 'k', linestyle = 'None', marker = '.', label='data')
                plt.xlabel('t')
                plt.ylabel(moments_list[mom_index_list[i]])
                ax.plot(t, opt_mu[mom_index_list[i]], color = 'r', label='optimised')
                ax.plot(t, start_mu[mom_index_list[i]], color = 'g', label='starting values')
            else:
                ax.plot(t_list, traj_list, color = 'k', linestyle = 'None', marker = '.')
            ax.yaxis.set_major_locator(MaxNLocator(5))           

    ax.legend(bbox_to_anchor=(1.0,-0.5))
    plt.tight_layout()
    fig.suptitle(plottitle)
    plt.show()
    



