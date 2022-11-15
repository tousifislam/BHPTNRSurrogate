##==============================================================================
## BHPTNRSur1dq1e4 : arXiv:2204.01972
## Description : utility file for surrogate model
## Author : Tousif Islam, Aug 2022 [tislam@umassd.edu / tousifislam24@gmail.com]
##==============================================================================

import numpy as np
from gwtools import gwtools as _gwtools
from gwtools.harmonics import sYlm as _sYlm
from . import nr_calibration as nrcalib

#----------------------------------------------------------------------------------------------------
def amp_ph_to_comp(amp,phase):
    """ Takes the amplitude and phase of the waveform and
    computes the compose them together"""
    
    full_wf = amp*np.exp(1j*phase)
    return full_wf

#----------------------------------------------------------------------------------------------------
def re_im_to_comp(re, im, m, orbital_phase):
    """ Takes the real and imaginary part of the waveform and
    combine them to obtain the coorbital frame waveform;
    then transform the wf into the inertial frame"""
    
    full_wf = (re+1j*im)*np.exp(1j*m*np.array(orbital_phase))
    return full_wf

#---------------------------------------------------------------------------------------------------- 
def geo_to_SI(t_geo, h_geo, M_tot, dist_mpc):
    """
    transforms the waveform from geomeric unit to physical unit
    given geoemtric time, geometric waveform, total mass M, distance dL
    """    
    # set constants
    G=_gwtools.G
    MSUN_SI = _gwtools.MSUN_SI
    PC_SI = _gwtools.PC_SI
    C_SI = _gwtools.c
    # Physical units
    M = M_tot * MSUN_SI
    dL = dist_mpc * PC_SI
    
    # scaling of time
    t_SI = t_geo * (G*M/C_SI**3)
    # scaling of strain for all modes
    strain_geo_to_SI = (G*M/C_SI**3)/dL
    h_SI={}
    for mode in h_geo.keys():
        h_SI[(mode)] = np.array(h_geo[mode])*strain_geo_to_SI
    
    return t_SI, h_SI

#---------------------------------------------------------------------------------------------------- 
def phase_rotation(h, delta_orb_phase):
    """
    performs an orbital phase rotation
    """
    h_rotated = {}
    
    for mode in h.keys():
        (l,m) = mode
        # calculate the corresponding phase rotation in respective modes
        phase_rot = m*delta_orb_phase
        # apply phase rotation
        h_rotated[mode] = h[mode] * np.exp(1j*phase_rot)
        
    return h_rotated

#---------------------------------------------------------------------------------------------------- 
def evaluate_on_sphere(theta, phi, h_dict):
    """evaluate on the sphere"""

    if theta is not None:
        if phi is None: raise ValueError('phi must have a value')
            
        hdict_sphere = {}
        for mode in h_dict.keys():
            (ell,m)=mode
            # compute spherical harmonics 
            sYlm_value =  _sYlm(-2,ll=ell,mm=m,theta=theta,phi=phi)
            # compute modes
            hdict_sphere[mode] = sYlm_value*h_dict[mode]
            
    return hdict_sphere

#---------------------------------------------------------------------------------------------------- 
def sum_modes(h_dict):
    """sum all the modes on a point in the sky"""
    
    h = np.zeros(len(h_dict[(2,2)]))
    for mode in h_dict.keys():
        h = h + h_dict[mode]
    return h


#---------------------------------------------------------------------------------------------------- 
def generate_negative_m_mode(h_dict):
    """ 
    For m>0 positive modes hp_mode,hc_mode use h(l,-m) = (-1)^l h(l,m)^* to compute the m<0 mode.
    See Eq. 78 of Kidder,Physical Review D 77, 044016 (2008), arXiv:0710.0614v1 [gr-qc].
    """

    h_dict_all_modes = {}
    
    for mode in h_dict.keys():
        (l,m)=mode
        # obtain postive m mode values
        h_dict_all_modes[(l,m)] = h_dict[mode]
        # sanity checks
        if (m==0):
            raise ValueError('m must be nonnegative. m<0 will be generated for you from the m>0 mode.')
        elif (m<0):
            raise ValueError('m must be nonnegative. m<0 will be generated for you from the m>0 mode.')
        # calculate negative m mode
        else:
            h_dict_all_modes[(l,-m)] = np.power(-1,l) * np.conjugate(h_dict[mode])

    return h_dict_all_modes


#----------------------------------------------------------------------------------------------------
def obtain_processed_output(X_calib, time, hsur_raw_dict, alpha_coeffs, 
                            beta_coeffs, alpha_beta_functional_form, calibrated,
                            M_tot, dist_mpc, orb_phase, inclination, mode_sum, neg_modes, lmax):
    """
    Function to process the output of raw surrogate to apply :
    (i) NR calibration;
    (ii) Conversion to SI units from geometric units;
    (iii) mode summation;
    """
        
    # when nr calibration is applied
    if calibrated==True:
        t_sur, hsur_dict = nrcalib.generate_calibrated_ppBHPT(X_calib, time, hsur_raw_dict, alpha_coeffs, 
                                                                  beta_coeffs, alpha_beta_functional_form)
        if lmax>5:
            print('WARNING : only modes up to \ell=5 are NR calibrated')
    # when no nr calibration is applied
    else:
        t_sur=np.array(time)
        hsur_dict = hsur_raw_dict
        print('WARNING : modes are NOT NR calibrated - waveforms only have 0PA contribution')

    # get all the negative m modes from postive m modes using symmetry
    if neg_modes:
        hsur_dict = generate_negative_m_mode(hsur_dict)

    # relevant for obtaining physical waveforms
    if M_tot is not None and dist_mpc is not None:
        t_sur, hsur_dict = geo_to_SI(t_sur, hsur_dict, M_tot, dist_mpc)
        # evaluate on the sphere
        if orb_phase is not None and inclination is not None:
            hsur_dict = evaluate_on_sphere(inclination, orb_phase, hsur_dict)

    # sum up the modes if it is asked
    if mode_sum==False:
        return t_sur, hsur_dict
    else:
        if M_tot is not None and dist_mpc is not None and orb_phase is not None and inclination is not None:
            h_summed = sum_modes(hsur_dict)
            return t_sur, h_summed
        
        