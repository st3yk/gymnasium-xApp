#!/usr/bin/env python3

import time
import datetime
import argparse
import signal
from lib.xAppBase import xAppBase


class MonRcApp(xAppBase):
    def __init__(self, http_server_port, rmr_port):
        super(MonRcApp, self).__init__(None, http_server_port, rmr_port)
        self.metrics = [
            "DRB.UEThpUl",
            "RRU.PrbUsedUl",
        ]
        self.debug = True
        self.state = 6 * []

    def my_subscription_callback(self, e2_agent_id, subscription_id, indication_hdr, indication_msg, kpm_report_style):
        indication_hdr = self.e2sm_kpm.extract_hdr_info(indication_hdr)
        meas_data = self.e2sm_kpm.extract_meas_data(indication_msg)

        if self.debug:
            print("\nRIC Indication Received from {} for Subscription ID: {}, KPM Report Style: {}".format(e2_agent_id, subscription_id, kpm_report_style))
            print("E2SM_KPM RIC Indication Content:")
            print("-ColletStartTime: ", indication_hdr['colletStartTime'])
            print("-Measurements Data:")

            granulPeriod = meas_data.get("granulPeriod", None)
            if granulPeriod is not None:
                print("-granulPeriod: {}".format(granulPeriod))

            for ue_id, ue_meas_data in meas_data["ueMeasData"].items():
                print("--UE_id: {}".format(ue_id))
                granulPeriod = ue_meas_data.get("granulPeriod", None)
                if granulPeriod is not None:
                    print("---granulPeriod: {}".format(granulPeriod))

                for metric_name, value in ue_meas_data["measData"].items():
                    print("---Metric: {}, Value: {}".format(metric_name, value))

    # Mark the function as xApp start function using xAppBase.start_function decorator.
    # It is required to start the internal msg receive loop.
    @xAppBase.start_function
    def start(self, e2_node_id, kpm_report_style, metric_names):
        report_period = 1000
        granul_period = 1000
        
        # xApp will use E2SM KPM Report Style 2 (UE-level) for all three UEs
        # It will store the last state for all of them to return it to the environment when asked
        subscription_callback = lambda agent, sub, hdr, msg: self.my_subscription_callback(agent, sub, hdr, msg, kpm_report_style)

        # dummy matching UE condition to get IDs of all connected UEs
        matchingUeConds = [{'testCondInfo': {'testType': ('ul-rSRP', 'true'), 'testExpr': 'lessthan', 'testValue': ('valueInt', 1000)}}]
        
        print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: {}, metrics: {}".format(e2_node_id, kpm_report_style, metric_names))
        self.e2sm_kpm.subscribe_report_service_style_4(e2_node_id, report_period, matchingUeConds, metric_names, granul_period, subscription_callback)


if __name__ == '__main__':
    # Config
    http_server_port = 8092
    rmr_port = 4562
    ran_func_id = 2
    kpm_report_style = 4
    # metrics = ["DRB.UEThpUl", "RRU.PrbUsedUl", "RRU.PrbAvailUl", "RRU.PrbTotUl"]
    metrics = ["DRB.UEThpUl", "RRU.PrbUsedUl"]
    e2_node_id = "gnbd_001_001_00019b_0"

    # Create the xApp
    xApp = MonRcApp(http_server_port, rmr_port)
    xApp.e2sm_kpm.set_ran_func_id(ran_func_id)

    # Connect exit signals.
    signal.signal(signal.SIGQUIT, xApp.signal_handler)
    signal.signal(signal.SIGTERM, xApp.signal_handler)
    signal.signal(signal.SIGINT, xApp.signal_handler)

    # Start the xApp
    xApp.start(e2_node_id, kpm_report_style, metrics)
    # Note: xApp will unsubscribe all active subscriptions at exit
