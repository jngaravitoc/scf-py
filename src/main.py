#!/usr/bin/env python3.8
"""
Pipeline to generate ascii files of the MW particles, LMC bound particles and
MW+LMC unbound particles

author: github/jngaravitoc
12/2019


    Code Features:
        - Compute BFE expansion from a collection of snapshots
        - It separates a satellite galaxy from a host galaxy 
        - Compute COM of satellite and host galaxy
        - Compute bound and satellite unbound particles
        - Run in parallel for the nlm list! 
    
    TODO:

        Parameter file:
            - Make different categories for Host and Satellite?
            - Think that if this is going to be general we might need more than
              one satellite. 

        Implement all optional outputs:
            - random satellite sample
            - output ascii files
            - what if the COM is provided?
            - use ids to track bound - unbound particles -- think about cosmo
              zooms
            - track bound mass fraction
            - write Gadget format file

        Implement checks:
            - equal mass particles (DONE)
            - com accuracy check
            - plot figure with com of satellite and host for every snapshot..
            - BFE monopole term amplitude -- compute nmax=20, lmax=0 and check
                larger term is 000

        Implement tests for every function**
        Implement parallel computation for bound satellite particles.
        * : fast to implement
        ** : may need some time to implement

        Paralleization:
            - Why results=pool() returns empty list if --ncores==1?

    - known issues:
        - currently multiprocessing return the following error when many
          particles are used: 
          struct.error: 'i' format requires -2147483648 <= number <= 2147483647

          This is a known issue of multiprocessing that apparently is solved in
          python3.8 
          see :
            https://stackoverflow.com/questions/47776486/python-struct-error-i-format-requires-2147483648-number-2147483647
"""

import numpy as np
import sys
import schwimmbad
import LMC_bounded as lmcb
import gadget_to_ascii as g2a
import io_snaps as ios
import coeff_parallel as cop
import allvars
from argparse import ArgumentParser
from quick_viz_check import scatter_plot


if __name__ == "__main__":

    parser = ArgumentParser(description="Parameters file for bfe-py")

    parser.add_argument("--param", dest="paramFile", default="config.yaml",
                       type=str, help="provide parameter file")


    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ncores", dest="n_cores", default=16,
                       type=int, help="Number of processes (uses multiprocessing).")
    group.add_argument("--mpi", dest="mpi", default=False,
                       action="store_true", help="Run with MPI.")
    global args
    args = parser.parse_args()
    
    # Loading paramfile 
    paramfile = args.paramFile
    params = allvars.readparams(paramfile)
    in_path = params[0]
    snapname = params[1]
    outpath = params[2]
    out_name = params[3]
    n_halo_part = params[4]
    npart_sample = params[5]
    nmax = params[6]
    lmax = params[7]
    rs = params[8]
    ncores = params[9]
    mpi = params[10]
    rcut_halo = params[11]
    init_snap=params[12]
    final_snap=params[13]
    SatBFE = params[14] 
    sat_rs = params[15]
    nmax_sat = params[16]
    lmax_sat = params[17]
    HostBFE = params[18]
    SatBoundParticles = params[19]
    HostSatUnboundPart = params[20]
    

    for i in range(init_snap, final_snap):
        print("**************************")

        # Loading data:
        halo = ios.read_snap_coordinates(in_path, snapname+"_{:03d}".format(i), n_halo_part, com_frame='MW', galaxy='MW')
        
        # Truncates halo:
        if rcut_halo>0:
            print("Truncating halo particles at {} kpc".format(rcut_halo))
            pos_halo_tr, vel_halo_tr, mass_tr, ids_tr = g2a.truncate_halo(halo[0], halo[1], halo[3], halo[4], rcut_halo)
            del halo
        else : 
            pos_halo_tr = halo[0]
            vel_halo_tr = halo[1]
            mass_tr = halo[3]
            ids_tr = halo[4]
        # Sampling halo
        if npart_sample>0: 
            print("Sampling halo particles with: {} particles".format(npart_sample))
            pos_halo_tr, vel_halo_tr, mass_tr = g2a.sample_halo(pos_halo_tr, vel_halo_tr, mass_tr, npart_sample) 
        
        # Truncating satellite
        if SatBFE == 1:
            satellite = ios.read_snap_coordinates(in_path, snapname+"_{:03d}".format(i), n_halo_part, com_frame='sat', galaxy='sat')
            pos_sat_tr, vel_sat_tr, mass_sat_tr, ids_sat_tr = g2a.truncate_halo(satellite[0], satellite[1], satellite[3], satellite[4], rcut_halo)
            pos_sat_em, vel_sat_em, mass_sat_em, ids_sat_em = g2a.npart_satellite(pos_sat_tr, vel_sat_tr, ids_sat_tr, mass_sat_tr[0], mass_tr[0])
            assert np.abs(mass_sat_em[0]/mass_tr[0]-1)<1E-3, 'Error: particle mass of satellite different to particle mass of the halo'

        #rint(len(pos_halo_tr))
        scatter_plot(outpath+snapname+"_{:03d}".format(i), pos_halo_tr)
        
        
        if write_snaps_ascii== True :
            out_snap_host = 'MW_{}_{}'.format(int(len(pos_halo_tr)/1E6), snapname+"{}".format(i))
            out_snap_sat= 'LMC_{}_{}'.format(int(len(pos_sat_em)/1E6), snapname+"{}".format(i))
            #write_log([n_halo_part, halo[3][0], len(pos_sample), mass_sample], [len(pos_sat_tr[0]), satellite[3][0], len(pos_sat_em), mass_sat_em])
            write_snap_txt(out_path_MW, out_snap_host, pos_halo_tr, vel_halo_tr, mass_tr, ids_tr)
            write_snap_txt(out_path_LMC, out_snap_sat, pos_sat_em, vel_sat_em, mass_sat_em, ids_sat_em)
            #write_snap_txt(out_path_LMC, out_snap_sat, satellite[0], satellite[1], satellite[3], satellite[4])
            lmc_bound = np.array([pos_bound[:,0], pos_bound[:,1], pos_bound[:,2],
                              vel_bound[:,0], vel_bound[:,1], vel_bound[:,2],
                              ids_bound]).T
           lmc_unbound = np.array([pos_unbound[:,0], pos_unbound[:,1], pos_unbound[:,2],
                                vel_unbound[:,0], vel_unbound[:,1], vel_unbound[:,2],
                                ids_unbound]).T
        # 'Combining satellite unbound particles with host particles')
        	
            mw_lmc_unbound = np.array([pos_host_sat[:,0], pos_host_sat[:,1], pos_host_sat[:,2], 
                                       vel_host_sat[:,0], vel_host_sat[:,1], vel_host_sat[:,2],
                                       mass_array]).T

        if ((SatBFE==1) & (SatBoundParticles ==1)):
            print('Computing satellite bound particles!')
            armadillo = lmcb.find_bound_particles(pos_sat_em, vel_sat_em, mass_sat_em, ids_sat_em, 10, 20, 20)
            print('Done: Computing satellite bound particles!')
            pos_bound = armadillo[0]
            N_part_bound = armadillo[1]
            ids_bound_part = armadillo[2]
            pos_unbound = armadillo[3]
            vel_unbound = armadillo[4]
            ids_unbound = armadillo[5] 
        
        # Pool for parallel computation! 
        pool = schwimmbad.choose_pool(mpi=args.mpi,
                                      processes=args.n_cores)

        if HostSatUnboundBFE == 1:
            print('Computing Host & satellite debris potential')
            # 'Combining satellite unbound particles with host particles')
            pos_host_sat = np.vstack((pos_halo_tr, pos_unbound))	
            # TODO : Check mass array?

            mass_array = np.ones(len(ids_unbound))*mass_sat_em[0]
            mass_Host_Debris = np.hstack((mass, mass_array))
            halo_debris_coeff = cop.Coeff_parallel(pos_host_sat, mass, rs, True, nmax, lmax)
            results_BFE_halo_debris = halo_debris_coeff.main(pool)
            print('Done computing Host & satellite debris potential')
            ios.write_coefficients(outpath+out_name+"snap_{:0>3d}.txt".format(i),\
                                   results_BFE_halo_debris, nmax, lmax, rs, mass[0])
        

        elif HostBFE == 1:
            print('Computing Host BFE')
            halo_coeff = cop.Coeff_parallel(pos_halo_tr, mass, rs, True, nmax, lmax)
            results_BFE_host = halo_coeff.main(pool)
            print('Done computing Host BFE')
            ios.write_coefficients(outpath+out_name+"snap_{:0>3d}.txt".format(i),\
                                   results_BFE_host, nmax, lmax, rs, mass[0])
        

        elif SatBFE == 1:
            print('Computing Sat BFE')
            mass_array = np.ones(len(ids_unbound))*mass_sat_em[0]
            sat_coeff = cop.Coeff_parallel(pos_unbounb, mass_array, sat_rs, True, \
                                           sat_nmax, sat_lmax)
            results_BFE_sat = sat_coeff.main(pool)
            print('Done computing Sat BFE')

            ios.write_coefficients(outpath+out_name+"snap_{:0>3d}.txt".format(i),\
                                   results_BFE_sat, nmax, lmax, rs, mass[0])
        


        
