#!/usr/bin/env python3.8
"""
bfe-py 
is a python code that computes BFE Hernquist expansion in idealized n-body simulations 
it works in parallel using python  multiprocessing.

This pipeline generates hdf5 files of the host particles, satellite bound particles and
MW--LMC unbound particles

author: github/jngaravitoc
12/2019 - 

"""

import numpy as np
import sys
import schwimmbad
import bfe.satellites as lmcb
import bfe.ios.gadget_to_ascii as g2a
import bfe.ios.io_snaps as ios
import bfe.coefficients.parallel_coefficients as cop
import allvars
from bfe.ios.com import re_center

from argparse import ArgumentParser
from quick_viz_check import scatter_plot, density_plot


def welcome_logo():
    print("         __                __              __                       __      __       __    ") 
    print("        / /\              /\ \            /\ \                     /\ \    /\ \     /\_\   ")
    print("       / /  \            /  \ \          /  \ \                   /  \ \   \ \ \   / / /   ")
    print("      / / /\ \          / /\ \ \        / /\ \ \                 / /\ \ \   \ \ \_/ / /    ")
    print("     / / /\ \ \        / / /\ \_\      / / /\ \_\   ____        / / /\ \_\   \ \___/ /     ")
    print("    / / /\ \_\ \      / /_/_ \/_/     / /_/_ \/_/ /\____/\     / / /_/ / /    \ \ \_/      ")
    print("   / / /\ \ \___\    / /____/\       / /____/\    \/____\/    / / /__\/ /      \ \ \       ")
    print("  / / /  \ \ \__/   / /\____\/      / /\____\/               / / /_____/        \ \ \      ")
    print(" / / /____\_\ \    / / /           / / /______              / / /                \ \ \     ")
    print("/ / /__________\  / / /           / / /_______\            / / /                  \ \_\    ")
    print("\/_____________/  \/_/            \/__________/            \/_/                    \/_/    \n")
    print("Hi! This is bfe-py v0.1 running!")
    return 0

if __name__ == "__main__":

    parser = ArgumentParser(description="Parameters file for bfe-py")

    parser.add_argument(
            "--param", dest="paramFile", default="config.yaml",
            type=str, help="provide parameter file")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
            "--ncores", dest="n_cores", default=16,
            type=int, help="Number of processes (uses multiprocessing).")
    group.add_argument("--mpi", dest="mpi", default=False,
                       action="store_true", help="Run with MPI.")
    global args
    args = parser.parse_args()

    # TODO: move all these variables to allvars and call it from there
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
    mmax = params[8]
    rs = params[9]
    ncores = params[10]
    mpi = params[11]
    rcut_halo = params[12]
    init_snap = params[13]
    final_snap = params[14]
    SatBFE = params[15]
    sat_rs = params[16]
    nmax_sat = params[17]
    lmax_sat = params[18]
    mmax_sat = params[19]
    HostBFE = params[20]
    SatBoundParticles = params[21]
    HostSatUnboundBFE = params[22]
    write_snaps_ascii = params[23]
    out_ids_bound_unbound_sat = params[24]
    plot_scatter_sample = params[25]
    npart_sample_satellite = params[26]
    snapformat = params[27]
    # rcut_sat = params[26]
    variance=params[28]
	# Printing welcome message
		

    for i in range(init_snap, final_snap):
        with open(outpath+'info.log', 'a') as out_log:
            out_log.write("**************************\n")
            out_log.write("loading snap {}{} \n".format(snapname, i))

            # *********************** Loading data: **************************
            
            if ((HostBFE == 1) | (HostSatUnboundBFE == 1)):
                out_log.write("reading host particles")
                halo = ios.read_snap_coordinates(
                        in_path, snapname+"_{:03d}".format(i),
                        n_halo_part, com_frame='host', galaxy='host', snapformat=snapformat)
                rcom_halo = halo[5]
                vcom_halo = halo[6]
                # Truncates halo:
                if rcut_halo > 0:
                    out_log.write(
                            "Truncating halo particles at {} kpc \n".format(
                                rcut_halo))

                    pos_halo_tr, vel_halo_tr, mass_tr, ids_tr \
                            = g2a.truncate_halo(
                                    halo[0], halo[1],
                                    halo[3], halo[4], rcut_halo)
                    del halo
                else:
                    pos_halo_tr = halo[0]
                    vel_halo_tr = halo[1]
                    mass_tr = halo[3]
                    ids_tr = halo[4]
                    del halo
                # Sampling halo

                if npart_sample > 0:
                    out_log.write(
                            "Sampling halo particles with: {} particles \n".format(
                                npart_sample))

                    pos_halo_tr, vel_halo_tr, mass_tr, ids_tr \
                            = g2a.sample_halo(
                                    pos_halo_tr, vel_halo_tr,
                                    mass_tr, npart_sample, ids_tr)
                out_log.write("Host halo particle mass {} \n".format(mass_tr[0]))

            # Truncating satellite for BFE computation
            if ((SatBFE == 1) | (HostSatUnboundBFE == 1)):
                out_log.write("reading satellite particles \n")
                
                satellite = ios.read_snap_coordinates(
                        in_path, snapname+"_{:03d}".format(i),
                        n_halo_part, com_frame='sat', galaxy='sat', snapformat=snapformat)

                rcom_sat = satellite[5]
                vcom_sat = satellite[6]
                pos_sat_tr, vel_sat_tr, mass_sat_tr, ids_sat_tr\
                        = g2a.truncate_halo(
                                satellite[0], satellite[1], satellite[3],
                                satellite[4], rcut_halo)

                if ((HostBFE == 1) | (HostSatUnboundBFE == 1)):

                    pos_sat_em, vel_sat_em, mass_sat_em, ids_sat_em\
                            = g2a.npart_satellite(
                                    pos_sat_tr, vel_sat_tr, ids_sat_tr,
                                    mass_sat_tr[0], mass_tr[0])

                    assert np.abs((mass_sat_em[0]/mass_tr[0])-1) < 1E-3,\
                            'Error: particle mass of satellite different to particle mass of the halo'

                if npart_sample_satellite > 0:
                    pos_sat_em, vel_sat_em, mass_sat_em, ids_sat_em\
                            = g2a.sample_halo(
                                    pos_sat_tr, vel_sat_tr, mass_sat_tr,
                                    npart_sample_satellite, ids_sat_tr)

                else :
                    pos_sat_em = pos_sat_tr
                    vel_sat_em = vel_sat_tr
                    mass_sat_em = mass_sat_tr
                    ids_sat_em = ids_sat_tr
                    
                    del(pos_sat_tr)
                    del(vel_sat_tr)
                    del(mass_sat_tr)
                    del(ids_sat_tr)

            if plot_scatter_sample == 1:
                # Plot 2d projections scatter plots

                if ((HostBFE == 1) | (HostSatUnboundBFE == 1)):
                    scatter_plot(
                            outpath+snapname+"_host_{:03d}".format(i),
                            pos_halo_tr)

                if SatBFE == 1:
                    scatter_plot(
                            outpath+snapname+"_sat_{:03d}".format(i), 
                            pos_sat_em)
                
                    
            #*************************  Compute BFE: ***************************** 
    
            if ((SatBFE == 1) & (SatBoundParticles == 1)):
                out_log.write("Computing satellite bound particles!\n")
                
                # *** Compute satellite bound paticles ***
                armadillo = lmcb.find_bound_particles(
                        pos_sat_em, vel_sat_em, mass_sat_em, ids_sat_em, 
                        sat_rs, nmax_sat, lmax_sat, ncores,
                        npart_sample = 100000)

                # npart_sample sets the number of particles to compute the
                # potential in each cpu more than 100000 usually generate memory
                # errors

                # removing old variables
                del(pos_sat_em)
                del(vel_sat_em)
                

                out_log.write('Done: Computing satellite bound particles! \n')
                pos_bound = armadillo[0]
                vel_bound = armadillo[1]
                ids_bound = armadillo[2]
                pos_unbound = armadillo[3]
                vel_unbound = armadillo[4]
                ids_unbound = armadillo[5]
                #rs_opt = armadillo[6]
                # mass arrays of bound and unbound particles
                N_part_bound = len(ids_bound)
                N_part_unbound = len(ids_unbound)
                mass_bound_array = np.ones(N_part_bound)*mass_sat_em[0]
                mass_unbound_array = np.ones(N_part_unbound)*mass_sat_em[0]
                out_log.write("Satellite particle mass {}\n".format(mass_sat_em[0]))    
                # Mass bound fractions
                Mass_bound = (N_part_bound/len(ids_sat_em))*np.sum(mass_sat_em)
                Mass_unbound = (N_part_unbound/len(ids_sat_em))*np.sum(mass_sat_em)
                Mass_fraction = (N_part_bound)/len(ids_sat_em)
                out_log.write("Satellite bound mass fraction {} \n".format(Mass_fraction))
                out_log.write("Satellite bound mass {} \n".format(Mass_bound))
                out_log.write("Satellite unbound mass {} \n".format(Mass_unbound))

                if plot_scatter_sample == 1:
                    out_log.write("plotting scatter plots of unbound and bound satellite particles \n")
                    scatter_plot(outpath+snapname+"_unbound_sat_{:03d}_nmax_{}".format(i, nmax_sat), pos_unbound)
                    scatter_plot(outpath+snapname+"_bound_sat_{:03d}_nmax{}".format(i, nmax_sat), pos_bound)
                    density_plot(outpath+snapname+"_density_unbound_sat_{:03d}_nmax{}".format(i, nmax_sat), pos_unbound)
                    density_plot(outpath+snapname+"_density_bound_sat_{:03d}_nmax{}".format(i, nmax_sat), pos_bound)
                
                
                if out_ids_bound_unbound_sat == 1:
                    out_log.write("writing satellite bound id \n")
                    np.savetxt(outpath+snapname+"_bound_sat_ids_{:03d}".format(i), ids_bound)

            if HostSatUnboundBFE == 1:
                pool_host_sat = schwimmbad.choose_pool(mpi=args.mpi,
                    processes=args.n_cores)
                out_log.write("Computing Host & satellite debris potential \n")
                # 'Combining satellite unbound particles with host particles')
                # recenter back satellite unbound particles to MW' COM
                pos_unbound_mw_frame = re_center(pos_unbound, -rcom_sat)
                
                #density_plot(outpath+snapname+"_unbound_mw_frame_{:03d}.png".format(i), 
                #             pos_unbound_mw_frame)

                #density_plot(outpath+snapname+"_unbound_lmc_frame_{:03d}.png".format(i), 
                #             pos_unbound)

                pos_host_sat = np.vstack((pos_halo_tr, pos_unbound_mw_frame))
                # TODO : Check mass array?
                density_plot(outpath+snapname+"_unbound_mw_lmc_frame_{:03d}.png".format(i), 
                             pos_host_sat)
                mass_Host_Debris = np.hstack((mass_tr, mass_unbound_array))
                np.savetxt(outpath+snapname+"halo_particles_{:03d}.txt".format(i), pos_halo_tr)
                np.savetxt(outpath+snapname+"debris_particles_{:03d}.txt".format(i), pos_unbound_mw_frame)
                #out_log.write("Debris_mass=" mass_unbound_array[0])
                #out_log.write("Halo_mass=" mass_tr[0])

                halo_debris_coeff = cop.Coeff_parallel(
                        pos_host_sat, mass_Host_Debris, rs, True, nmax, lmax)
            
                results_BFE_halo_debris = halo_debris_coeff.main(pool_host_sat)
                out_log.write("Done computing Host & satellite debris potential")
                ios.write_coefficients_hdf5(
                        outpath+out_name+"_host_sat_unbound_snap_{:03d}".format(i),
                        results_BFE_halo_debris, [nmax, lmax, mmax], [rs, mass_Host_Debris[0], 0],  rcom_halo)
            
    
            if HostBFE == 1:
                pool_host = schwimmbad.choose_pool(mpi=args.mpi,
                    processes=args.n_cores)
                out_log.write("Computing Host BFE \n")
                halo_coeff = cop.Coeff_parallel(
                        pos_halo_tr, mass_tr, rs, variance, nmax, lmax)
                
                results_BFE_host = halo_coeff.main(pool_host)
                print(np.shape(results_BFE_host)) 
                out_log.write("Done computing Host BFE")
                ios.write_coefficients_hdf5(
                        outpath+out_name+"_host_snap_{:03d}".format(i),
                        results_BFE_host, [nmax, lmax, mmax], [rs, mass_tr[0], 0],  rcom_halo)
        

            if ((SatBFE == 1) & (SatBoundParticles == 1)):
                out_log.write("Computing Sat BFE \n")
                pool_sat = schwimmbad.choose_pool(mpi=args.mpi,
                                                  processes=args.n_cores)
                sat_coeff = cop.Coeff_parallel(
                        pos_bound, mass_bound_array, sat_rs, variance, nmax_sat, lmax_sat)

                results_BFE_sat = sat_coeff.main(pool_sat)
                out_log.write("Done computing Sat BFE \n")
    
                ios.write_coefficients_hdf5(
                        outpath+out_name+"_sat_bound_snap_{:03d}.txt".format(i),
                        results_BFE_sat, [nmax_sat, lmax_sat, mmax_sat], [sat_rs,
                        mass_bound_array[0], 0], satellite[5])
        
            if ((SatBFE == 1) & (SatBoundParticles == 0)):
                out_log.write("Computing Sat BFE \n")
                pool_sat = schwimmbad.choose_pool(mpi=args.mpi,
                                                  processes=args.n_cores)
                sat_coeff = cop.Coeff_parallel(
                        pos_sat_em, mass_sat_em, sat_rs, variance, nmax_sat, lmax_sat)

                results_BFE_sat = sat_coeff.main(pool_sat)
                out_log.write("Done computing Sat BFE \n")
    
                ios.write_coefficients_hdf5(
                        outpath+out_name+"_sat_snap_{:03d}".format(i),
                        results_BFE_sat, [lmax_sat, lmax_sat, mmax_sat], [sat_rs,
                        mass_sat_em[0], 0], satellite[5])
        
            
    
            # TODO : check this flag 
            # Write snapshots ascii files
            if write_snaps_ascii == 1:
    
                # Write Host snap 
                if HostBFE == 1: 
                    out_snap_host = 'MW_{}_{}'.format(
                            int(len(pos_halo_tr)/1E6), snapname+"_{}".format(i))

                    g2a.write_snap_txt(
                            outpath, out_snap_host, pos_halo_tr,
                            vel_halo_tr, mass_tr, ids_tr)

                if SatBFE == 1:
                    out_snap_sat_bound= 'LMC_bound_{}'.format(
                            snapname+"_{}".format(i))

                    # Combining satellite unbound particles with host particles
                    g2a.write_snap_txt(
                        outpath, out_snap_sat_bound, pos_bound,
                        vel_bound, mass_bound_array, ids_bound)
