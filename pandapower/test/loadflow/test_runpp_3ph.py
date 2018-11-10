# -*- coding: utf-8 -*-
"""
Created on Wed May  2 17:06:25 2018
Tests 3 phase power flow algorithm
@author: sghosh
"""
import pandapower as pp
import numpy as np
import pytest
from pandapower.pf.runpp_3ph import combine_X012
from pandapower.create import create_load_3ph, create_load
from pandapower.pf.runpp_3ph import runpp_3ph
import copy
from pandapower.pf.makeYbus import makeYbus 
from pandapower.pf.runpp_3ph import I0_from_V012,I1_from_V012,I2_from_V012


@pytest.fixture
def net():
    V_base = 110              # 110kV Base Voltage
    kVA_base = 100000         # 100 MVA
#    I_base = (kVA_base/V_base) * 1e-3           # in kA
    net = pp.create_empty_network(sn_kva = kVA_base )
    
    pp.create_bus(net, vn_kv = V_base, index=1)
    pp.create_bus(net, vn_kv = V_base, index=5)
    
    pp.create_ext_grid(net, bus=1, vm_pu= 1.0, s_sc_max_mva=5000, rx_max=0.1)
    net.ext_grid["r0x0_max"] = 0.1
    net.ext_grid["x0x_max"] = 1.0
    
    pp.create_std_type(net, {"r0_ohm_per_km": 0.0848, "x0_ohm_per_km": 0.4649556, "c0_nf_per_km":
                             230.6,"max_i_ka": 0.963, "r_ohm_per_km": 0.0212,
                             "x_ohm_per_km": 0.1162389, "c_nf_per_km":  230},
                       "example_type")
    pp.create_line(net, from_bus = 1, to_bus = 5, length_km = 50.0, std_type="example_type")

    create_load_3ph(net, 5, p_kw_A=50000, q_kvar_A=50000, p_kw_B=10000, q_kvar_B=15000,
                       p_kw_C=10000, q_kvar_C=5000)
    return net


def check_it(net):
    assert np.allclose(net.res_bus_3ph.vmA_pu[~np.isnan(net.res_bus_3ph.vmA_pu)],
                       np.array([0.96742893, 0.74957533]))
    assert np.allclose(net.res_bus_3ph.vmB_pu[~np.isnan(net.res_bus_3ph.vmB_pu)],
                       np.array([1.01302766, 1.09137945]))
    assert np.allclose(net.res_bus_3ph.vmC_pu[~np.isnan(net.res_bus_3ph.vmC_pu)],
                       np.array([1.019784, 1.05124282]))

    assert abs(net.res_line_3ph.iA_from_ka.values[0] - 1.34212045) < 1e-5
    assert abs(net.res_line_3ph.iA_to_ka.values[0]   - 1.48537916) < 1e-5
    
    assert abs(net.res_line_3ph.iB_from_ka.values[0] - 0.13715552) < 1e-5
    assert abs(net.res_line_3ph.iB_to_ka.values[0]   - 0.26009611) < 1e-5
               
    assert abs(net.res_line_3ph.iC_from_ka.values[0] - 0.22838401) < 1e-5
    assert abs(net.res_line_3ph.iC_to_ka.values[0]   - 0.1674634) < 1e-5
        
    assert abs(net.res_line_3ph.pA_from_kw.values[0]*1e-3   - 55.70772301) < 1e-4
    assert abs(net.res_line_3ph.pA_to_kw.values[0]*1e-3     - (-49.999992954)) < 1e-4
    assert abs(net.res_line_3ph.qA_from_kvar.values[0]*1e-3 - 60.797262682) < 1e-4
    assert abs(net.res_line_3ph.qA_to_kvar.values[0]*1e-3   - (-49.999959283)) < 1e-4
               
    assert abs(net.res_line_3ph.pB_from_kw.values[0]*1e-3   - 8.7799379802) < 1e-4
    assert abs(net.res_line_3ph.pB_to_kw.values[0]*1e-3     - (-9.9999996625)) < 1e-4           
    assert abs(net.res_line_3ph.qB_from_kvar.values[0]*1e-3 - (-0.88093549983)) < 1e-4
    assert abs(net.res_line_3ph.qB_to_kvar.values[0]*1e-3   - (-15.000000238)) < 1e-4
               
    assert abs(net.res_line_3ph.pC_from_kw.values[0]*1e-3   - 9.3739293122) < 1e-4
    assert abs(net.res_line_3ph.pC_to_kw.values[0] *1e-3    - (-10.000000161)) < 1e-4
    assert abs(net.res_line_3ph.qC_from_kvar.values[0]*1e-3 - (-11.441663679)) < 1e-4
    assert abs(net.res_line_3ph.qC_to_kvar.values[0] *1e-3  - (-4.9999997418)) < 1e-4
           	        
    assert abs(net.res_line_3ph.loading_percentA.values[0] - 154.2452) < 1e-2
    assert abs(net.res_line_3ph.loading_percentB.values[0] - 27.00894) < 1e-2
    assert abs(net.res_line_3ph.loading_percentC.values[0] - 23.71589) < 1e-2
    assert abs(net.res_line_3ph.loading_percent.values[0]  - 154.2452) < 1e-2


def test_2bus_network(net):
    "#-o---o"
    pp.add_zero_impedance_parameters(net)
    runpp_3ph(net)
    check_it(net)    


def test_2bus_network_single_isolated_busses(net):
    "#-o---o o x"
    pp.create_bus(net, vn_kv=110)
    pp.create_bus(net, vn_kv=110, in_service=False)
    pp.add_zero_impedance_parameters(net)
    runpp_3ph(net)
    check_it(net)    


def test_2bus_network_isolated_net_part(net):
    "#-o---o o---o"
    b1 = pp.create_bus(net, vn_kv=110)
    b2 = pp.create_bus(net, vn_kv=110)
    pp.create_line(net, from_bus=b1, to_bus=b2, length_km = 50.0, std_type="example_type")
    create_load_3ph(net, b2, p_kw_A=50000, q_kvar_A=50000, p_kw_B=10000, q_kvar_B=15000,
                   p_kw_C=10000, q_kvar_C=5000)
    pp.add_zero_impedance_parameters(net)
    runpp_3ph(net)
    check_it(net)


def test_2bus_network_singel_oos_bus(net):
    "#-o---x---o"
    b1 = pp.create_bus(net, vn_kv=110)
    net.bus.loc[5, "in_service"] = False
    pp.create_line(net, from_bus=5, to_bus=b1, length_km = 10.0, std_type="example_type")
    create_load_3ph(net, b1, p_kw_A=-5000, q_kvar_A=5000, p_kw_B=-1000, q_kvar_B=1500,
                    p_kw_C=-1000, q_kvar_C=500)
    pp.add_zero_impedance_parameters(net)
    assert runpp_3ph(net)[3]["success"]


def test_4bus_network():
    V_base = 110                     # 110kV Base Voltage
    kVA_base = 100000                      # 100 MVA

    net = pp.create_empty_network(sn_kva = kVA_base )
    # =============================================================================
    # Main Program
    # =============================================================================
    busn  =  pp.create_bus(net, vn_kv = V_base, name = "busn")
    busk  =  pp.create_bus(net, vn_kv = V_base, name = "busk")
    busm =  pp.create_bus(net, vn_kv = V_base, name = "busm")
    busp =  pp.create_bus(net, vn_kv = V_base, name = "busp")
    pp.create_ext_grid(net, bus=busn, vm_pu=1.0, name="Grid Connection", s_sc_max_mva=5000, 
                       rx_max=0.1)
    net.ext_grid["r0x0_max"] = 0.1
    net.ext_grid["x0x_max"] = 1.0
    
    pp.create_std_type(net, {"r0_ohm_per_km": 0.0848, "x0_ohm_per_km": 0.4649556, "c0_nf_per_km":\
        230.6,   "max_i_ka": 0.963, "r_ohm_per_km": 0.0212, "x_ohm_per_km": 0.1162389,
                 "c_nf_per_km":  230}, "example_type1")
    
    pp.create_std_type(net, {"r0_ohm_per_km" : .3048, "x0_ohm_per_km" : 0.6031856, 
                             "c0_nf_per_km" : 140.3, "max_i_ka": 0.531, 
                              "r_ohm_per_km" : .0762, "x_ohm_per_km" : 0.1507964
                            , "c_nf_per_km" : 140}, "example_type2")
    pp.create_std_type(net, {"r0_ohm_per_km" : .154, "x0_ohm_per_km" : 0.5277876
                             , "c0_nf_per_km" : 170.4, "max_i_ka": 0.741, 
                              "r_ohm_per_km" : .0385, "x_ohm_per_km" : 0.1319469
                             , "c_nf_per_km" : 170}, "example_type3")
    
    pp.create_std_type(net, {"r0_ohm_per_km" : .1005, "x0_ohm_per_km" : 0.4900884
                             , "c0_nf_per_km":  200.5, "max_i_ka" : 0.89
                             , "r_ohm_per_km": .0251, "x_ohm_per_km" : 0.1225221
                             , "c_nf_per_km" : 210}, "example_type4")
    
    pp.create_line(net, from_bus = busn, to_bus = busm, length_km = 1.0, std_type="example_type3")
    pp.create_line(net, from_bus = busn, to_bus = busp, length_km = 1.0, std_type="example_type3")
    pp.create_line(net, from_bus = busn, to_bus = busk, length_km = 1.0, std_type="example_type4")
    pp.create_line(net, from_bus = busk, to_bus = busm, length_km = 1.0, std_type="example_type1")
    pp.create_line(net, from_bus = busk, to_bus = busp, length_km = 1.0, std_type="example_type2")
    pp.add_zero_impedance_parameters(net)
    
    create_load_3ph(net, busk, p_kw_A=50000, q_kvar_A=20000, p_kw_B=80000, q_kvar_B=60000,
                       p_kw_C=20000, q_kvar_C=5000)
    create_load_3ph(net, busm, p_kw_A=50000, q_kvar_A=50000, p_kw_B=10000, q_kvar_B=15000,
                       p_kw_C=10000, q_kvar_C=5000)
    create_load_3ph(net, busp, p_kw_A=50000, q_kvar_A=20000, p_kw_B=60000, q_kvar_B=20000,
                       p_kw_C=10000, q_kvar_C=5000)
    runpp_3ph(net)
    
    v_a_pf = np.array([0.98085729,  0.97828577,  0.97774307,  0.9780892])
    v_b_pf = np.array([0.97711997,  0.97534651,  0.97648197,  0.97586805])
    v_c_pf = np.array([1.04353786,  1.04470864,  1.04421233,  1.04471106])
    
    assert np.allclose(net.res_bus_3ph.vmA_pu,v_a_pf,atol=1e-4 )
    assert np.allclose(net.res_bus_3ph.vmB_pu,v_b_pf,atol=1e-4 )
    assert np.allclose(net.res_bus_3ph.vmC_pu,v_c_pf,atol=1e-4 )
    
    i_a_f_pf = np.array([0.98898804851	,    0.87075816277		,	0.95760407055	,	0.21780921494 	,	0.03712221482])
    i_b_f_pf = np.array([0.68943734300	,	1.03463205150 	,	1.14786582480	,	0.42795802661	,	0.10766244499])
    i_c_f_pf = np.array([0.19848961274	,	0.19072621839	,	0.24829126422	,	0.03706411747	,	0.03093504641])

    i_a_t_pf = np.array([0.99093993074  ,   0.87210778953,	0.95975383019,0.22229618812	,0.03446870607])
    i_b_t_pf = np.array([0.69146383889	,	1.03599166860	,	1.15028039760	,	0.42603286136 	,	0.10500385951])
    i_c_t_pf = np.array([0.19966503490	,	0.19188990522 	,	0.24975552990	,	0.03771702877 	,	0.03179428313])
    assert np.allclose(net.res_line_3ph.iA_from_ka,i_a_f_pf,atol=1e-4)
    assert np.allclose(net.res_line_3ph.iB_from_ka,i_b_f_pf,atol=1e-4)
    assert np.allclose(net.res_line_3ph.iC_from_ka,i_c_f_pf,atol=1e-4)
    
    assert np.allclose(net.res_line_3ph.iA_to_ka,i_a_t_pf,atol=1e-4)
    assert np.allclose(net.res_line_3ph.iB_to_ka,i_b_t_pf,atol=1e-4)
    assert np.allclose(net.res_line_3ph.iC_to_ka,i_c_t_pf,atol=1e-4)
    
    p_a_f_pf =np.array([49.87434308300	,	49.59359423400	,	50.87938854400	,	0.23292404144	,	0.52956690003])*1e3
    p_b_f_pf =np.array([33.86579548300	,	58.53676841800	,	57.53628872500	,	-23.88471674400	,	1.44846451670])*1e3
    p_c_f_pf =np.array([12.44659879200	,	11.97553940900	,	15.54470530900	,	-2.45255094990	,	-1.98645639180]) *1e3
    
    q_a_f_pf =np.array([36.16562612500	,	21.96967200100	,	31.13888556700	,	13.53037091600	,	-2.24476446080])*1e3
    q_b_f_pf =np.array([26.14426519000	,	26.37559958400	,	41.99378843000	,	-11.49972059800	,	-6.50971484920])*1e3
    q_c_f_pf =np.array([4.25746427990	,	4.04458872690	,	5.39758513360	,	0.17971664973	,	0.51637909987]) *1e3
    
    p_a_t_pf =np.array([-49.75842138300	,	-49.47110288600	,	-50.76249094400	,	-0.24157861683	,	-0.52889711581]) *1e3
    p_b_t_pf =np.array([-33.90236497100	,	-58.55284704700	,	-57.56374776900	,	23.90236496800	,	-1.44715294780])*1e3
    p_c_t_pf =np.array([-12.45155362100	,	-11.98669515800	,	-15.56099267200	,	2.45155361280	,	1.98669514890]) *1e3
    
    q_a_t_pf =np.array([-36.19862687800	,	-22.07474008400	,	-31.28560645900	,	-13.80137312400	,	2.07474008110]) *1e3
    q_b_t_pf =np.array([-26.25675246200	,	-26.34476810500	,	-41.99056453000	,	11.25675246600	,	6.34476811700])*1e3
    q_c_t_pf =np.array([-4.50384237760	,	-4.29078446670	,	-5.69609575190	,	-0.49615762485	,	-0.70921553583]) *1e3
    
    assert np.allclose(net.res_line_3ph.pA_from_kw,p_a_f_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.pB_from_kw,p_b_f_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.pC_from_kw,p_c_f_pf,atol=1e-2)
    
    assert np.allclose(net.res_line_3ph.qA_from_kvar,q_a_f_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.qB_from_kvar,q_b_f_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.qC_from_kvar,q_c_f_pf,atol=1e-2)
    
    assert np.allclose(net.res_line_3ph.pA_to_kw,p_a_t_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.pB_to_kw,p_b_t_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.pC_to_kw,p_c_t_pf,atol=1e-2)
    
    assert np.allclose(net.res_line_3ph.qA_to_kvar,q_a_t_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.qB_to_kvar,q_b_t_pf,atol=1e-2)
    assert np.allclose(net.res_line_3ph.qC_to_kvar,q_c_t_pf,atol=1e-2)
    
    load_a_pf = np.array([133.73010000000	,	117.69340000000	,	107.83750000000	,	23.08372000000	,	6.99100100000]) 
    load_b_pf = np.array([93.31496000000	,	139.80990000000	,	129.24500000000	,	44.44009000000	,	20.27541000000]) 
    load_c_pf = np.array([26.94535000000	,	25.89607000000	,	28.06242000000	,	3.91661800000	,	5.98762400000]) 
    load_pf = np.array([133.73010000000	,	139.80990000000	,	129.24500000000	,	44.44009000000	,	20.27541000000]) 
    assert np.allclose(net.res_line_3ph.loading_percentA ,load_a_pf ,atol=1e-2)
    assert np.allclose(net.res_line_3ph.loading_percentB ,load_b_pf,atol=1e-2 ) 	
    assert np.allclose(net.res_line_3ph.loading_percentC ,load_c_pf,atol=1e-2 ) 
    assert np.allclose(net.res_line_3ph.loading_percent ,load_pf,atol=1e-2 )



def test_in_serv_load():
    V_base = 110                     # 110kV Base Voltage
    kVA_base = 100000                      # 100 MVA
#    I_base = (kVA_base/V_base) * 1e-3           # in kA
    V_base_res = V_base/np.sqrt(3)
    I_base_res = kVA_base/V_base_res*1e-3
    net = pp.create_empty_network(sn_kva = kVA_base )
    
    busn  =  pp.create_bus(net, vn_kv = V_base, name = "busn", index=1)
    busk  =  pp.create_bus(net, vn_kv = V_base, name = "busk", index=5)
    pp.create_bus(net, vn_kv=20., in_service=False)
    pp.create_bus(net, vn_kv=20., in_service=True)
    
    
    pp.create_ext_grid(net, bus=busn, vm_pu= 1.0, name="Grid Connection",
                       s_sc_max_mva=5000, rx_max=0.1)
    net.ext_grid["r0x0_max"] = 0.1
    net.ext_grid["x0x_max"] = 1.0
    
    pp.create_std_type(net, {"r0_ohm_per_km": 0.0848, "x0_ohm_per_km": 0.4649556, "c0_nf_per_km":\
        230.6,"max_i_ka": 0.963, "r_ohm_per_km": 0.0212, "x_ohm_per_km": 0.1162389,
                 "c_nf_per_km":  230}, "example_type")
    
    create_load_3ph(net, busk, p_kw_A=50000, q_kvar_A=50000, p_kw_B=10000, q_kvar_B=15000,
                       p_kw_C=10000, q_kvar_C=5000)
    
    pp.create_line(net, from_bus = busn, to_bus = busk, length_km = 50.0, std_type="example_type")
    
    pp.add_zero_impedance_parameters(net)
    
    runpp_3ph(net)
    
    assert np.allclose(net.res_bus_3ph.vmA_pu[~np.isnan(net.res_bus_3ph.vmA_pu)], np.array([0.96742893, 0.74957533]))
    assert np.allclose(net.res_bus_3ph.vmB_pu[~np.isnan(net.res_bus_3ph.vmB_pu)], np.array([1.01302766, 1.09137945]))
    assert np.allclose(net.res_bus_3ph.vmC_pu[~np.isnan(net.res_bus_3ph.vmC_pu)], np.array([1.019784, 1.05124282]))

    assert abs(net.res_line_3ph.iA_from_ka.values[0] - 1.34212045) < 1e-5
    assert abs(net.res_line_3ph.iA_to_ka.values[0]   - 1.48537916) < 1e-5
    
    assert abs(net.res_line_3ph.iB_from_ka.values[0] - 0.13715552) < 1e-5
    assert abs(net.res_line_3ph.iB_to_ka.values[0]   - 0.26009611) < 1e-5
               
    assert abs(net.res_line_3ph.iC_from_ka.values[0] - 0.22838401) < 1e-5
    assert abs(net.res_line_3ph.iC_to_ka.values[0]   - 0.1674634) < 1e-5
        
    assert abs(net.res_line_3ph.pA_from_kw.values[0]*1e-3   - 55.70772301) < 1e-4
    assert abs(net.res_line_3ph.pA_to_kw.values[0]*1e-3     - (-49.999992954)) < 1e-4
    assert abs(net.res_line_3ph.qA_from_kvar.values[0]*1e-3 - 60.797262682) < 1e-4
    assert abs(net.res_line_3ph.qA_to_kvar.values[0]*1e-3   - (-49.999959283)) < 1e-4
               
    assert abs(net.res_line_3ph.pB_from_kw.values[0]*1e-3   - 8.7799379802) < 1e-4
    assert abs(net.res_line_3ph.pB_to_kw.values[0]*1e-3     - (-9.9999996625)) < 1e-4           
    assert abs(net.res_line_3ph.qB_from_kvar.values[0]*1e-3 - (-0.88093549983)) < 1e-4
    assert abs(net.res_line_3ph.qB_to_kvar.values[0]*1e-3   - (-15.000000238)) < 1e-4
               
    assert abs(net.res_line_3ph.pC_from_kw.values[0]*1e-3   - 9.3739293122) < 1e-4
    assert abs(net.res_line_3ph.pC_to_kw.values[0] *1e-3    - (-10.000000161)) < 1e-4
    assert abs(net.res_line_3ph.qC_from_kvar.values[0]*1e-3 - (-11.441663679)) < 1e-4
    assert abs(net.res_line_3ph.qC_to_kvar.values[0] *1e-3  - (-4.9999997418)) < 1e-4
           	        
    assert abs(net.res_line_3ph.loading_percentA.values[0] - 154.2452) < 1e-2
    assert abs(net.res_line_3ph.loading_percentB.values[0] - 27.00894) < 1e-2
    assert abs(net.res_line_3ph.loading_percentC.values[0] - 23.71589) < 1e-2
    assert abs(net.res_line_3ph.loading_percent.values[0]  - 154.2452) < 1e-2
    
    create_load_3ph(net, busk, p_kw_A=50000, q_kvar_A=100000, p_kw_B=29000, q_kvar_B=38000,
                   p_kw_C=10000, q_kvar_C=5000, in_service=False)

    runpp_3ph(net)
    
    assert np.allclose(net.res_bus_3ph.vmA_pu[~np.isnan(net.res_bus_3ph.vmA_pu)], np.array([0.96742893, 0.74957533]))
    assert np.allclose(net.res_bus_3ph.vmB_pu[~np.isnan(net.res_bus_3ph.vmB_pu)], np.array([1.01302766, 1.09137945]))
    assert np.allclose(net.res_bus_3ph.vmC_pu[~np.isnan(net.res_bus_3ph.vmC_pu)], np.array([1.019784, 1.05124282]))

    assert abs(net.res_line_3ph.iA_from_ka.values[0] - 1.34212045) < 1e-5
    assert abs(net.res_line_3ph.iA_to_ka.values[0]   - 1.48537916) < 1e-5
    
    assert abs(net.res_line_3ph.iB_from_ka.values[0] - 0.13715552) < 1e-5
    assert abs(net.res_line_3ph.iB_to_ka.values[0]   - 0.26009611) < 1e-5
               
    assert abs(net.res_line_3ph.iC_from_ka.values[0] - 0.22838401) < 1e-5
    assert abs(net.res_line_3ph.iC_to_ka.values[0]   - 0.1674634) < 1e-5
        
    assert abs(net.res_line_3ph.pA_from_kw.values[0]*1e-3   - 55.70772301) < 1e-4
    assert abs(net.res_line_3ph.pA_to_kw.values[0]*1e-3     - (-49.999992954)) < 1e-4
    assert abs(net.res_line_3ph.qA_from_kvar.values[0]*1e-3 - 60.797262682) < 1e-4
    assert abs(net.res_line_3ph.qA_to_kvar.values[0]*1e-3   - (-49.999959283)) < 1e-4
               
    assert abs(net.res_line_3ph.pB_from_kw.values[0]*1e-3   - 8.7799379802) < 1e-4
    assert abs(net.res_line_3ph.pB_to_kw.values[0]*1e-3     - (-9.9999996625)) < 1e-4           
    assert abs(net.res_line_3ph.qB_from_kvar.values[0]*1e-3 - (-0.88093549983)) < 1e-4
    assert abs(net.res_line_3ph.qB_to_kvar.values[0]*1e-3   - (-15.000000238)) < 1e-4
               
    assert abs(net.res_line_3ph.pC_from_kw.values[0]*1e-3   - 9.3739293122) < 1e-4
    assert abs(net.res_line_3ph.pC_to_kw.values[0] *1e-3    - (-10.000000161)) < 1e-4
    assert abs(net.res_line_3ph.qC_from_kvar.values[0]*1e-3 - (-11.441663679)) < 1e-4
    assert abs(net.res_line_3ph.qC_to_kvar.values[0] *1e-3  - (-4.9999997418)) < 1e-4
           	        
    assert abs(net.res_line_3ph.loading_percentA.values[0] - 154.2452) < 1e-2
    assert abs(net.res_line_3ph.loading_percentB.values[0] - 27.00894) < 1e-2
    assert abs(net.res_line_3ph.loading_percentC.values[0] - 23.71589) < 1e-2
    assert abs(net.res_line_3ph.loading_percent.values[0]  - 154.2452) < 1e-2

# =============================================================================
# Creating more loads in the same bus is tricky. Even in power factory some scenarios fail depending
# on the values given
# =============================================================================
#    create_load_3ph(net, busk, p_kw_A=50000, q_kvar_A=10000, p_kw_B=10000, q_kvar_B=5000,
#           p_kw_C=10000, q_kvar_C=5000, in_service=True)
#    count,V012_it,I012_it,ppci0,Y1_pu = runpp_3ph(net)
#    
#    V_abc_new,I_abc_new,Sabc_changed = show_results(V_base,kVA_base,count,ppci0,Y1_pu,V012_it,I012_it)
#    Sabc_powerFactory, Vabc_powerFactory, Iabc_powerFactory = results_2bus_PowerFactory()
#    load_mapping(net)
#    
#def test_transformer_3ph_diff_kvabase():
#    hv_base = 20                     # 110kV Base Voltage
#    lv_base = 0.4
#    kVA_base = 1000                     # 100 MVA
##    I_base = (kVA_base/V_base) * 1e-3           # in kA
#    vector_group = "Yyn"
##    hv_base_res = hv_base/np.sqrt(3)
##    lv_base_res = lv_base/np.sqrt(3)
#
#    net = pp.create_empty_network(sn_kva = kVA_base )
#    
#    bushv  =  pp.create_bus(net, vn_kv = hv_base, zone=vector_group, name = "bushv", index=1)
#    buslv  =  pp.create_bus(net, vn_kv = lv_base, zone=vector_group, name = "buslv", index=5)
##    pp.create_bus(net, vn_kv=20., in_service=False)
##    pp.create_bus(net, vn_kv=20., in_service=True)
#    
#    pp.create_ext_grid(net, bushv, s_sc_max_mva=5000, rx_max=0.1)
#    net.ext_grid["r0x0_max"] = 0.1
#    net.ext_grid["x0x_max"] = 1.0
#    
#    transformer_type = copy.copy(pp.load_std_type(net, "0.63 MVA 20/0.4 kV","trafo"))
#    transformer_type.update({"vsc0_percent": 6, "vscr0_percent": 1.095238, "mag0_percent": 100,
#                     "mag0_rx": 0., "vector_group": vector_group,"vscr_percent": 1.095238,
#                     "shift_degree": 0 })
#    pp.create_std_type(net, transformer_type, vector_group, "trafo")
#    pp.create_transformer(net, bushv, buslv, std_type=vector_group, parallel=1,
#                          index=pp.get_free_id(net.trafo)+1)
##    pp.create_transformer(net, bushv, buslv, std_type=vector_group, in_service=False)
#    
#    create_load_3ph(net, buslv, p_kw_A=300, q_kvar_A=20, p_kw_B=100, q_kvar_B=50,
#                       p_kw_C=100, q_kvar_C=30)
#    pp.add_zero_impedance_parameters(net)
#    count,V012_it_1k,I012_it_1k,ppci0, Y0_pu_1k,Y1_pu_1k,Y2_pu_1k = runpp_3ph(net)
#    
#    net.sn_kva = 100000
#    
#    count,V012_it_100k,I012_it_100k,ppci0, Y0_pu_100k,Y1_pu_100k,Y2_pu_100k = runpp_3ph(net)
#    
#    print ('\n\n\nV',V012_it_1k/V012_it_100k,'\n\n\n I ',I012_it_1k/I012_it_100k,\
#           '\n\n\nY0',Y0_pu_1k/Y0_pu_100k,'\n\n\nY1',Y1_pu_1k/Y1_pu_100k,'\n\n\nY2',\
#           Y2_pu_1k/Y2_pu_100k)
#    
#    net.sn_kva = 1000
#    vector_group = "YNyn"
#    net = pp.create_empty_network(sn_kva = kVA_base )
#    
#    bushv  =  pp.create_bus(net, vn_kv = hv_base, zone=vector_group, name = "bushv", index=1)
#    buslv  =  pp.create_bus(net, vn_kv = lv_base, zone=vector_group, name = "buslv", index=5)
##    pp.create_bus(net, vn_kv=20., in_service=False)
##    pp.create_bus(net, vn_kv=20., in_service=True)
#    
#    pp.create_ext_grid(net, bushv, s_sc_max_mva=5000, rx_max=0.1)
#    net.ext_grid["r0x0_max"] = 0.1
#    net.ext_grid["x0x_max"] = 1.0
#    
#    transformer_type = copy.copy(pp.load_std_type(net, "0.63 MVA 20/0.4 kV","trafo"))
#    transformer_type.update({"vsc0_percent": 6, "vscr0_percent": 1.095238, "mag0_percent": 100,
#                     "mag0_rx": 0., "vector_group": vector_group,"vscr_percent": 1.095238,
#                     "shift_degree": 0, "si0_hv_partial": 0.9 })
#    pp.create_std_type(net, transformer_type, vector_group, "trafo")
#    pp.create_transformer(net, bushv, buslv, std_type=vector_group, parallel=1,
#                          index=pp.get_free_id(net.trafo)+1)
##    pp.create_transformer(net, bushv, buslv, std_type=vector_group, in_service=False)
#    
#    create_load_3ph(net, buslv, p_kw_A=300, q_kvar_A=20, p_kw_B=100, q_kvar_B=50,
#                       p_kw_C=100, q_kvar_C=30)
#    pp.add_zero_impedance_parameters(net)
#    count,V012_it_1k,I012_it_1k,ppci0, Y0_pu_1k,Y1_pu_1k,Y2_pu_1k = runpp_3ph(net)
#    
#    net.sn_kva = 100000
#    vector_group = "YNyn"
#    count,V012_it_100k,I012_it_100k,ppci0, Y0_pu_100k,Y1_pu_100k,Y2_pu_100k = runpp_3ph(net)
#    print ('\n\n\n YNyn \n\n\nV',V012_it_1k/V012_it_100k,'\n\n\n I ',I012_it_1k/I012_it_100k,\
#       '\n\n\nY0',Y0_pu_1k/Y0_pu_100k,'\n\n\nY1',Y1_pu_1k/Y1_pu_100k,'\n\n\nY2',\
#       Y2_pu_1k/Y2_pu_100k)


def test_3ph_bus_mapping_order():
    net = pp.create_empty_network()
    
    b2 = pp.create_bus(net, vn_kv=0.4, index=4)
    pp.create_bus(net, vn_kv=0.4, in_service=False, index=3)
    b1 = pp.create_bus(net, vn_kv=0.4, index=7)
    
    pp.create_ext_grid(net, b1, vm_pu=1.0, s_sc_max_mva=10, rx_max=0.1)
    net.ext_grid["x0x_max"] = 1.
    net.ext_grid["r0x0_max"] = 0.1
    pp.create_std_type(net, {"r_ohm_per_km":0.1013, "x_ohm_per_km": 0.06911504,
                             "c_nf_per_km": 690, "g_us_per_km": 0, "max_i_ka": 0.44,
                             "c0_nf_per_km": 312.4, "r0_ohm_per_km": 0.4053,
                             "x0_ohm_per_km": 0.2764602},"N2XRY 3x185sm 0.6/1kV")
    
    pp.create_line(net, b1, b2, 1.0, std_type="N2XRY 3x185sm 0.6/1kV", index=4)
    pp.create_line(net, b1, b2, 1.0, std_type="N2XRY 3x185sm 0.6/1kV", index=3, in_service=False)
    pp.create_line(net, b1, b2, 1.0, std_type="N2XRY 3x185sm 0.6/1kV", index=7)
    pp.add_zero_impedance_parameters(net)
    pp.create_load(net, b2, p_kw=30, q_kvar=30)
    pp.runpp(net)
    runpp_3ph(net)
    
    assert np.allclose(net.res_bus_3ph.vmA_pu.values, net.res_bus.vm_pu.values, equal_nan=True)
    assert net.res_bus_3ph.index.tolist() == net.res_bus.index.tolist()
    
    assert net.res_line_3ph.index.tolist() == net.res_line.index.tolist()
    assert np.allclose(net.res_line.p_from_kw, net.res_line_3ph.pA_from_kw +
                                               net.res_line_3ph.pB_from_kw +
                                               net.res_line_3ph.pC_from_kw )
    assert np.allclose(net.res_line.loading_percent, net.res_line_3ph.loading_percentA)  

    
def test_3ph_two_bus_line_powerfactory():
    net = pp.create_empty_network()
    
    b1 = pp.create_bus(net, vn_kv=0.4)
    b2 = pp.create_bus(net, vn_kv=0.4)
    
    pp.create_ext_grid(net, b1, vm_pu=1.0, s_sc_max_mva=10, rx_max=0.1)
    net.ext_grid["x0x_max"] = 1.
    net.ext_grid["r0x0_max"] = 0.1
    pp.create_std_type(net, {"r_ohm_per_km":0.1013, "x_ohm_per_km": 0.06911504,
                             "c_nf_per_km": 690, "g_us_per_km": 0, "max_i_ka": 0.44,
                             "c0_nf_per_km": 312.4, "r0_ohm_per_km": 0.4053,
                             "x0_ohm_per_km": 0.2764602}, "N2XRY 3x185sm 0.6/1kV")
    
    pp.create_line(net, b1, b2, 0.4, std_type="N2XRY 3x185sm 0.6/1kV")
    pp.add_zero_impedance_parameters(net)
    pp.create_load(net, b2, p_kw=10, q_kvar=10)
    pp.create_load_3ph(net, b2, p_kw_A=20, q_kvar_A=10, p_kw_B=15, q_kvar_B=5, p_kw_C=25,
                       q_kvar_C=10)
    
    runpp_3ph(net)
    
    assert np.allclose(net.res_bus_3ph.vmA_pu, np.array([0.99939853552, 0.97401782343]))
    assert np.allclose(net.res_bus_3ph.vmB_pu, np.array([1.0013885141, 0.98945593737]))
    assert np.allclose(net.res_bus_3ph.vmC_pu, np.array([0.99921580141, 0.96329605983]))

    assert abs(net.res_line_3ph.iA_from_ka.values[0] - 0.11946088987) < 1e-5
    assert abs(net.res_line_3ph.iA_to_ka.values[0]   - 0.1194708224) < 1e-5
    
    assert abs(net.res_line_3ph.iB_from_ka.values[0] - 0.08812337783) < 1e-5
    assert abs(net.res_line_3ph.iB_to_ka.values[0]   - 0.088131567331) < 1e-5
               
    assert abs(net.res_line_3ph.iC_from_ka.values[0] - 0.14074226065) < 1e-5
    assert abs(net.res_line_3ph.iC_to_ka.values[0]   - 0.14075063601) < 1e-5
        
    assert abs(net.res_line_3ph.pA_from_kw.values[0]   - 23.810539354) < 1e-2
    assert abs(net.res_line_3ph.pA_to_kw.values[0]     + 23.333142958) < 1e-2
    assert abs(net.res_line_3ph.qA_from_kvar.values[0] - 13.901720672) < 1e-2
    assert abs(net.res_line_3ph.qA_to_kvar.values[0]   + 13.332756527) < 1e-2
               
    assert abs(net.res_line_3ph.pB_from_kw.values[0]   - 18.55791658) < 1e-2
    assert abs(net.res_line_3ph.pB_to_kw.values[0]     + 18.333405987) < 1e-2           
    assert abs(net.res_line_3ph.qB_from_kvar.values[0] - 8.421814704) < 1e-2
    assert abs(net.res_line_3ph.qB_to_kvar.values[0]   + 8.333413919) < 1e-2
               
    assert abs(net.res_line_3ph.pC_from_kw.values[0]   - 29.375192747) < 1e-2
    assert abs(net.res_line_3ph.pC_to_kw.values[0]     + 28.331643666) < 1e-2
    assert abs(net.res_line_3ph.qC_from_kvar.values[0] - 13.852398586) < 1e-2
    assert abs(net.res_line_3ph.qC_to_kvar.values[0]   + 13.332422725) < 1e-2
               
    assert abs(net.res_line_3ph.loading_percentA.values[0] - 27.1525) < 1e-2
    assert abs(net.res_line_3ph.loading_percentB.values[0] - 20.0299) < 1e-2
    assert abs(net.res_line_3ph.loading_percentC.values[0] - 31.98878) < 1e-2
    assert abs(net.res_line_3ph.loading_percent.values[0]  - 31.98878) < 1e-2
    
def check_results(net, vc, result):
    res_vm_kv = np.concatenate(
            (
            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].vmA_pu,
            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].vmB_pu,
            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].vmC_pu,
#            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].pA_kw*1e-3,
#            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].qA_kvar*1e-3,
#            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].pB_kw*1e-3,
#            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].qB_kvar*1e-3,
#            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].pC_kw*1e-3,
#            net.res_bus_3ph[(net.bus.zone==vc)&(net.bus.in_service)].qC_kvar*1e-3
            )
            ,axis =0)
    if not np.allclose(result, res_vm_kv,atol=1e-4):
        raise ValueError("Incorrect results for vector group %s"%vc, res_vm_kv, result)
        
def make_nw(net,vectorgroup):
        hv_base = 20                     # 110kV Base Voltage
        lv_base = 0.4
        bushv  =  pp.create_bus(net, vn_kv = hv_base, zone=vectorgroup, name = "bushv")
        buslv  =  pp.create_bus(net, vn_kv = lv_base, zone=vectorgroup, name = "buslv")
    #    pp.create_bus(net, vn_kv=20., in_service=False)
    #    pp.create_bus(net, vn_kv=20., in_service=True)
        
        pp.create_ext_grid(net, bushv, s_sc_max_mva=5000, rx_max=0.1)
        net.ext_grid["r0x0_max"] = 0.1
        net.ext_grid["x0x_max"] = 1.0
        
        transformer_type = copy.copy(pp.load_std_type(net, "0.63 MVA 20/0.4 kV","trafo"))
        transformer_type.update({"vsc0_percent": 6, "vscr0_percent": 1.095238, "mag0_percent": 100,
                         "mag0_rx": 0., "vector_group": vectorgroup,"vscr_percent": 1.095238,
                         "shift_degree": 0, "si0_hv_partial": 0.9 })
        pp.create_std_type(net, transformer_type, vectorgroup, "trafo")
        t1= pp.create_transformer(net, bushv, buslv, std_type=vectorgroup, parallel=1,
                              index=pp.get_free_id(net.trafo)+1)
    #    pp.create_transformer(net, bushv, buslv, std_type=vector_group, in_service=False)
        
        create_load_3ph(net, buslv, p_kw_A=300, q_kvar_A=20, p_kw_B=100, q_kvar_B=50,
                           p_kw_C=100, q_kvar_C=30)
        pp.add_zero_impedance_parameters(net)
        return t1
        
def test_trafo_vg_loadflow():
    
# =============================================================================
# TODO: Check why there is formation of 2x1 Y0 bus matrix for other vector groups
# It has something to do with Y sh for these groups    
# =============================================================================
    results = {
#                "Yy": [	0.999933012433371,1.25037438180859,1.00002589218568,1.54325333471415,1.00004109872575,0.426542038619223	]
#                "Yyn":  [	0.999945441976376,1.22794573109855,1.00002125565888,1.4416173022977,1.00003330458372,0.464803132596897	]
#                ,"Yd":  [	0.999933012433371,1.25037438180859,1.00002589218568,1.54325333471415,1.00004109872575,0.426542038619223	]
#                ,"YNy": [	0.999933012433371,1.25037438180859,1.00002589218568,1.54325333471415,1.00004109872575,0.426542038619223	]
                "YNyn":[	0.999989798411917,0.974535554759052,0.999998062978948,0.979767191100436,1.00001214446541,0.98580613030435\
#                        ,0.29998199048,0.30491398063,0.019995651922,0.046418929571,0.099999883488,0.10140597436,0.04999993784,0.054212417817,0.099999915123,0.10148829148,0.029999966177,0.032762701427	
                        ]

#                ,"YNd": [	0.999933012433371,1.25037438180859,1.00002589218568,1.54325333471415,1.00004109872575,0.426542038619223	]
#                ,"Dy":  [	0.999933012433371,1.25037438180859,1.00002589218568,1.54325333471415,1.00004109872575,0.426542038619223	]
#                ,"Dyn": [	0.999994464210383,0.974485419076184,0.999960730788854,0.979873700533758,1.00004480678672,0.985749706670833	]
#                ,"Dd":  [	0.999933012433371,1.25037438180859,1.00002589218568,1.54325333471415,1.00004109872575,0.426542038619223	]

               }
    for vc in results.keys():
        net = pp.create_empty_network() 
        make_nw(net, vc)
        runpp_3ph(net)
        print(net.res_bus_3ph)
#        try:
#             runpp_3ph(net)
#        except:
#             raise UserWarning("Did not converge after adding transformer with vector group %s"%vc)
    
    for vc, result in results.items():
        check_results(net, vc, result)


def test_2trafos():
    net = pp.create_empty_network() 
    make_nw(net, "YNyn")
    make_nw(net, "YNyn")
    runpp_3ph(net)
    

def test_3ph_isolated_nodes():
    V_base = 110  # 110kV Base Voltage
    kVA_base = 100000  # 100 MVA
    net = pp.create_empty_network(sn_kva=kVA_base)

    busn = pp.create_bus(net, vn_kv=V_base, name="busn", index=1)
    busx = pp.create_bus(net, vn_kv=20., in_service=True, index=2, name="busx")
    busk = pp.create_bus(net, vn_kv=V_base, name="busk", index=5)
    busl = pp.create_bus(net, vn_kv=V_base, name="busl", index=6)
    pp.create_bus(net, vn_kv=20., in_service=False, index=3)
    busy = pp.create_bus(net, vn_kv=20., in_service=True, index=0, name="busy")

    pp.create_ext_grid(net, bus=busn, vm_pu=1.0, name="Grid Connection",
                       s_sc_max_mva=5000, rx_max=0.1)
    net.ext_grid["r0x0_max"] = 0.1
    net.ext_grid["x0x_max"] = 1.0

    pp.create_std_type(net, {"r0_ohm_per_km": 0.0848, "x0_ohm_per_km": 0.4649556, "c0_nf_per_km": \
        230.6, "max_i_ka": 0.963, "r_ohm_per_km": 0.0212, "x_ohm_per_km": 0.1162389,
                             "c_nf_per_km": 230}, "example_type")

    # Loads on supplied buses
    create_load_3ph(net, busk, p_kw_A=50000, q_kvar_A=50000, p_kw_B=10000, q_kvar_B=15000,
                    p_kw_C=10000, q_kvar_C=5000)
    create_load(net, bus=busl, p_kw=7000, q_kvar=70, name="Load 1")

    # Loads on unsupplied buses
    # create_load(net, bus=busy, p_kw=0, q_kvar=0, name="Load Y")
    create_load(net, bus=busy, p_kw=70000, q_kvar=70000, name="Load Y")
    # create_load_3ph(net, busx, p_kw_A=5000, q_kvar_A=5000, p_kw_B=1000, q_kvar_B=1500,
    #                 p_kw_C=1000, q_kvar_C=500, name="Load X")

    pp.create_line(net, from_bus=busn, to_bus=busk, length_km=50.0, std_type="example_type")
    pp.create_line(net, from_bus=busl, to_bus=busk, length_km=50.0, std_type="example_type")

    pp.add_zero_impedance_parameters(net)

    r = runpp_3ph(net)

    assert r[3]["success"]
    assert np.allclose(net.res_bus_3ph.T[[0, 2, 3]].T[["vmA_pu", "vaA_degree", "vmB_pu", "vaB_degree", "vmC_pu", "vaC_degree"]], np.nan, equal_nan=True)
    assert np.allclose(net.res_bus_3ph.T[[0, 2, 3]].T[["pA_kw", "qA_kvar", "pB_kw", "qB_kvar", "pC_kw", "qC_kvar"]], 0.0)


# def test_3bus_trafo_network():
#     vector_groups = ["YNyn"]
#     # Todo: Extend with other vector groups
#
#     for vector_group in vector_groups:
#         net = pp.create_empty_network()
#         hv_base = 20  # 110kV Base Voltage
#         lv_base = 0.4
#         bushv = pp.create_bus(net, vn_kv=hv_base, zone=vector_group, name="bushv")
#         buslv = pp.create_bus(net, vn_kv=lv_base, zone=vector_group, name="buslv")
#         busn = pp.create_bus(net, vn_kv=lv_base, zone=vector_group, name="busn")
#
#         pp.create_ext_grid(net, bushv, s_sc_max_mva=5000, rx_max=0.1)
#         net.ext_grid["r0x0_max"] = 0.1
#         net.ext_grid["x0x_max"] = 1.0
#
#         transformer_type = copy.copy(pp.load_std_type(net, "0.63 MVA 20/0.4 kV", "trafo"))
#         transformer_type.update({"vsc0_percent": 6, "vscr0_percent": 1.095238, "mag0_percent": 100,
#                                  "mag0_rx": 0., "vector_group": vector_group, "vscr_percent": 1.095238,
#                                  "shift_degree": 0, "si0_hv_partial": 0.9})
#         pp.create_std_type(net, {"r_ohm_per_km": 0.1013, "x_ohm_per_km": 0.06911504,
#                                  "c_nf_per_km": 690, "g_us_per_km": 0, "max_i_ka": 0.44,
#                                  "c0_nf_per_km": 312.4, "r0_ohm_per_km": 0.4053,
#                                  "x0_ohm_per_km": 0.2764602}, "N2XRY 3x185sm 0.6/1kV")
#
#         pp.create_std_type(net, transformer_type, vector_group, "trafo")
#         pp.create_transformer(net, bushv, buslv, std_type=vector_group, parallel=1,
#                                    index=pp.get_free_id(net.trafo) + 1)
#         pp.create_line(net, from_bus=buslv, to_bus=busn, length_km=1, std_type="N2XRY 3x185sm 0.6/1kV")
#
#         create_load_3ph(net, busn, p_kw_A=-20, q_kvar_A=10, p_kw_B=20, q_kvar_B=-10, p_kw_C=15, q_kvar_C=5)
#         pp.add_zero_impedance_parameters(net)
#         runpp_3ph(net, trafo_loading="current")
#
#         if not np.allclose(net["res_trafo_3ph"][["iA_lv_ka", "iB_lv_ka", "iC_lv_ka"]], net["res_line_3ph"][["iA_from_ka", "iB_from_ka", "iC_from_ka"]], atol=1e-4):
#             raise ValueError("Incorrect phase currents for vector group %s" % vector_group)

if __name__ == "__main__":
    pytest.main(["test_runpp_3ph.py"])