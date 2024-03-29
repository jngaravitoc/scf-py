import yaml
import numpy as np

def readparams(paramfile):
    with open(paramfile) as f:
        d = yaml.safe_load(f)
    
    inpath = d["inpath"]
    snapname = d["snapname"]
    outpath = d["outpath"]
    outname = d["outname"]
    npartHalo = d["npartHalo"]
    samplePart = d["samplePart"]
    nmax = d["nmax"]
    lmax = d["lmax"]
    mmax = d["mmax"]
    rs = d["rs"]
    ncores = d["ncores"]
    mpi = d["mpi"]
    rhaloCut = d["rhaloCut"]
    initSnap = d["initSnap"]
    finalSnap = d["finalSnap"]
    SatBFE = d["SatBFE"] 
    sat_rs = d["Satrs"]
    nmax_sat = d["nmaxSat"]
    lmax_sat = d["nmaxSat"]
    mmax_sat = d["nmaxSat"]
    HostBFE = d["HostBFE"]
    SatBoundParticles = d["SatBoundParticles"]
    HostSatUnboundPart = d["HostSatUnboundPart"]
    write_snaps_ascii = d["WriteSnapsAscii"]
    out_ids_bound_unbound_sat = d["OutIdsBoundUnbound"]
    plot_scatter_sample = d["PlotScatterSample"]
    samplePartSat = d["samplePartSat"]
    snapformat = d["snapformat"]
    variance = d["variance"]

    assert type(inpath)==str, "inpath parameter  must be a string"
    assert type(snapname)==str, "snapname parameter must be a string"
    assert type(outpath)==str, "outpath parameter must be a string"
    assert type(outname)==str, "outname parameter must be a string"
    assert type(npartHalo)==int, "npartHalo parameter must be an integer"
    assert type(samplePart)==int, "samplePart parameter must be an integer"
    assert type(npartHalo)==int, "npartHalo parameter must be an integer"
    assert type(nmax)==int, "nmax parameter must be an integer"
    assert type(lmax)==int, "lmax parameter must be an integer"
    assert type(mmax)==int, "mmax parameter must be an integer"
    assert type(rs)==float, "rs parameter must be a float"
    assert type(ncores)==int, "ncores parameter must be an integer"
    assert type(mpi)==int, "mpi parameter must be an integer"
    assert ((type(rhaloCut)==float) | (type(rhaloCut)==int)) , "rhaloCut parameter must be a float"
    assert type(initSnap)==int, "initSnap parameter must be an integer"
    assert type(finalSnap)==int, "finalSnap parameter must be an integer"
    assert type(SatBFE)==int, "SatBFE parameter must be an integer"
    assert type(snapformat)==int, "snap format must be an integer 0, 1, 2"
    assert snapformat <= 3, "snap format must be an integer 0, 1, 2"
    assert type(variance) == bool, "variance format must be bool"
    return [inpath, snapname, outpath, outname, npartHalo, samplePart, nmax,
            lmax, mmax, rs, ncores, mpi, rhaloCut, initSnap, finalSnap, SatBFE,
            sat_rs, nmax_sat, lmax_sat, mmax_sat, HostBFE, SatBoundParticles,
            HostSatUnboundPart, write_snaps_ascii, out_ids_bound_unbound_sat, 
            plot_scatter_sample, samplePartSat, snapformat, variance]

