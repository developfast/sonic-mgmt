import logging
import pytest

from files.helper import run_pfc_test
from tests.common.helpers.assertions import pytest_assert, pytest_require
from tests.common.fixtures.conn_graph_facts import conn_graph_facts,\
    fanout_graph_facts
from tests.common.snappi.snappi_fixtures import snappi_api_serv_ip, snappi_api_serv_port,\
    snappi_api, snappi_testbed_config
from tests.common.snappi.qos_fixtures import prio_dscp_map, all_prio_list, lossless_prio_list,\
    lossy_prio_list
from tests.common.reboot import reboot
from tests.common.platform.processes_utils import wait_critical_processes
from tests.common.utilities import wait_until

logger = logging.getLogger(__name__)

pytestmark = [ pytest.mark.topology('tgen') ]

def test_pfc_single_lossless_headroom(snappi_api,
                                        snappi_testbed_config,
                                        conn_graph_facts,
                                        fanout_graph_facts,
                                        duthosts,
                                        rand_one_dut_hostname,
                                        rand_one_dut_portname_oper_up,
                                        enum_dut_lossless_prio,
                                        all_prio_list,
                                        prio_dscp_map,
                                        pfc_pause_quanta_values):
    """
    Test headroom capacity for DUT for a single lossless priority

    Args:
        snappi_api (pytest fixture): SNAPPI session
        snappi_testbed_config (pytest fixture): testbed configuration information
        conn_graph_facts (pytest fixture): connection graph
        fanout_graph_facts (pytest fixture): fanout graph
        duthosts (pytest fixture): list of DUTs
        rand_one_dut_hostname (str): hostname of DUT
        rand_one_dut_portname_oper_up (str): port to test, e.g., 's6100-1|Ethernet0'
        enum_dut_lossless_prio (str): lossless priority to test, e.g., 's6100-1|3'
        all_prio_list (pytest fixture): list of all the priorities
        prio_dscp_map (pytest fixture): priority vs. DSCP map (key = priority).
        pfc_pause_quanta_values (pytest fixture): dictionary of pfc_delay values, 
                                                  and delay responses e.g. {1:True, 2:False}

    Returns:
        N/A
    """

    pytest_require(pfc_pause_quanta_values is not None, 
                    "Skip this testcase since pause quanta values have not been configured yet")
    dut_hostname, dut_port = rand_one_dut_portname_oper_up.split('|')
    dut_hostname2, lossless_prio = enum_dut_lossless_prio.split('|')
    pytest_require(rand_one_dut_hostname == dut_hostname == dut_hostname2,
                   "Priority and port are not mapped to the expected DUT")

    testbed_config, port_config_list = snappi_testbed_config
    duthost = duthosts[rand_one_dut_hostname]
    lossless_prio = int(lossless_prio)

    pause_prio_list = [lossless_prio]
    test_prio_list = [lossless_prio]
    bg_prio_list = [p for p in all_prio_list]
    bg_prio_list.remove(lossless_prio)

    """ Modify pfc pause quanta """
    l1_config = testbed_config.layer1[0]
    pytest_require(len(l1_config.port_names) > 2,
                   "Skip this testcase since only one Rx and Tx port have been configured")
    pfc = l1_config.flow_control.ieee_802_1qbb

    for pause_quanta, headroom_test_result in pfc_pause_quanta_values.items():
        pfc.pfc_delay = pause_quanta
        headroom_test_params = [pause_quanta, headroom_test_result]

        run_pfc_test(api=snappi_api,
                    testbed_config=testbed_config,
                    port_config_list=port_config_list,
                    conn_data=conn_graph_facts,
                    fanout_data=fanout_graph_facts,
                    duthost=duthost,
                    dut_port=dut_port,
                    global_pause=False,
                    pause_prio_list=pause_prio_list,
                    test_prio_list=test_prio_list,
                    bg_prio_list=bg_prio_list,
                    prio_dscp_map=prio_dscp_map,
                    test_traffic_pause=True,
                    headroom_test_params=headroom_test_params)


def test_pfc_pause_multi_lossless_headroom(snappi_api,
                                       snappi_testbed_config,
                                       conn_graph_facts,
                                       fanout_graph_facts,
                                       duthosts,
                                       rand_one_dut_hostname,
                                       rand_one_dut_portname_oper_up,
                                       lossless_prio_list,
                                       lossy_prio_list,
                                       prio_dscp_map,
                                       pfc_pause_quanta_values):
    """
    Test headroom capacity for DUT for multiple lossless priorities

    Args:
        snappi_api (pytest fixture): SNAPPI session
        snappi_testbed_config (pytest fixture): testbed configuration information
        conn_graph_facts (pytest fixture): connection graph
        fanout_graph_facts (pytest fixture): fanout graph
        duthosts (pytest fixture): list of DUTs
        rand_one_dut_hostname (str): hostname of DUT
        rand_one_dut_portname_oper_up (str): port to test, e.g., 's6100-1|Ethernet0'
        lossless_prio_list (pytest fixture): list of all the lossless priorities
        lossy_prio_list (pytest fixture): list of all the lossy priorities
        prio_dscp_map (pytest fixture): priority vs. DSCP map (key = priority).
        pfc_pause_quanta_values (pytest fixture): dictionary of pfc_delay values, 
                                                  and delay responses e.g. {1:True, 2:False}

    Returns:
        N/A
    """

    pytest_require(pfc_pause_quanta_values is not None, 
                    "Skip this testcase since pause quanta values have not been configured yet")
    dut_hostname, dut_port = rand_one_dut_portname_oper_up.split('|')
    pytest_require(rand_one_dut_hostname == dut_hostname,
                   "Port is not mapped to the expected DUT")

    testbed_config, port_config_list = snappi_testbed_config
    duthost = duthosts[rand_one_dut_hostname]
    pause_prio_list = lossless_prio_list
    test_prio_list = lossless_prio_list
    bg_prio_list = lossy_prio_list

    """ Modify pfc pause quanta """
    l1_config = testbed_config.layer1[0]
    pytest_require(len(l1_config.port_names) > 2,
                   "Skip this testcase since only one Rx and Tx port have been configured")
    pfc = l1_config.flow_control.ieee_802_1qbb

    for pause_quanta, headroom_test_result in pfc_pause_quanta_values.items():
        pfc.pfc_delay = pause_quanta
        headroom_test_params = [pause_quanta, headroom_test_result]

        run_pfc_test(api=snappi_api,
                    testbed_config=testbed_config,
                    port_config_list=port_config_list,
                    conn_data=conn_graph_facts,
                    fanout_data=fanout_graph_facts,
                    duthost=duthost,
                    dut_port=dut_port,
                    global_pause=False,
                    pause_prio_list=pause_prio_list,
                    test_prio_list=test_prio_list,
                    bg_prio_list=bg_prio_list,
                    prio_dscp_map=prio_dscp_map,
                    test_traffic_pause=True,
                    headroom_test_params=headroom_test_params)
