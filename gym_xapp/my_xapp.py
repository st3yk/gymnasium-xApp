#!/usr/bin/env python3

import time
import datetime
import argparse
import signal
from lib.xAppBase import xAppBase


class MonRcApp(xAppBase):
    def __init__(self, http_server_port=8092, rmr_port=4560):
        super(MonRcApp, self).__init__(None, http_server_port, rmr_port)
        self.debug = True
        self.state = 6 * []
        self.e2_node_id = "gnbd_001_001_00019b_0"
        self.metrics = ["DRB.UEThpDl", "RRU.PrbUsedDl", "NokDl", "McsDl"]
        self.cnt = 0
        self.max_thp = 33485
        self.max_prb = 45

    def my_subscription_callback(self, e2_agent_id, subscription_id, indication_hdr, indication_msg):
        indication_hdr = self.e2sm_kpm.extract_hdr_info(indication_hdr)
        meas_data = self.e2sm_kpm.extract_meas_data(indication_msg)
        thp_ul, used_prbs = [], []

        if self.debug:
            print("\nRIC Indication Received from {} for Subscription ID: {}, KPM Report Style: 4".format(e2_agent_id, subscription_id))
            print("E2SM_KPM RIC Indication Content:")
            print("-ColletStartTime: ", indication_hdr['colletStartTime'])
            print("-Measurements Data:")

        granulPeriod = meas_data.get("granulPeriod", None)
        if granulPeriod is not None and self.debug:
            print("-granulPeriod: {}".format(granulPeriod))

        for ue_id, ue_meas_data in meas_data["ueMeasData"].items():
            if self.debug:
                print("--UE_id: {}".format(ue_id))
            granulPeriod = ue_meas_data.get("granulPeriod", None)
            if granulPeriod is not None and self.debug:
                print("---granulPeriod: {}".format(granulPeriod))

            for metric_name, value in ue_meas_data["measData"].items():
                if self.debug:
                    print("---Metric: {}, Value: {}".format(metric_name, value))
                if metric_name == "DRB.UEThpUl":
                    thp_ul.append(round(value[0]/self.max_thp,2))
                elif metric_name == "RRU.PrbUsedUl":
                    used_prbs.append(round(value[0]/self.max_prb, 2))
        self.state = thp_ul + used_prbs
        # if self.debug:
        #     print(f"Current state: {self.state}")
        # self.cnt += 1
        # if self.cnt % 5 == 1:
        #     self.set_prb(1, 15 * (self.cnt % 2))

    def get_state(self):
        return state

    def set_prb(self, ue_id, prb_ratio):
        if self.debug:
            print(f"Setting slice level prb quota to {prb_ratio} for ue {ue_id}")
        self.e2sm_rc.control_slice_level_prb_quota(
            self.e2_node_id,
            ue_id,
            min_prb_ratio=1,
            max_prb_ratio=max(1,prb_ratio),
            dedicated_prb_ratio=max(1,prb_ratio),
            ack_request=1,
        )

    # Mark the function as xApp start function using xAppBase.start_function decorator.
    # It is required to start the internal msg receive loop.
    @xAppBase.start_function
    def start(self):
        report_period = 1000
        granul_period = 1000
        # xApp will use E2SM KPM Report Style 4
        # It will store the last state for all of them to return it to the environment when asked
        subscription_callback = lambda agent, sub, hdr, msg: self.my_subscription_callback(agent, sub, hdr, msg)

        # dummy matching UE condition to get IDs of all connected UEs
        matchingUeConds = [{'testCondInfo': {'testType': ('ul-rSRP', 'true'), 'testExpr': 'lessthan', 'testValue': ('valueInt', 1000)}}]
        
        if self.debug:
            print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: 4, metrics: {}".format(self.e2_node_id, self.metrics))
        self.e2sm_kpm.subscribe_report_service_style_4(self.e2_node_id, report_period, matchingUeConds, self.metrics, granul_period, subscription_callback)


if __name__ == '__main__':
    # Create the xApp
    xApp = MonRcApp()
    ran_func_id = 2
    xApp.e2sm_kpm.set_ran_func_id(ran_func_id)

    # Connect exit signals.
    signal.signal(signal.SIGQUIT, xApp.signal_handler)
    signal.signal(signal.SIGTERM, xApp.signal_handler)
    signal.signal(signal.SIGINT, xApp.signal_handler)

    # Start the xApp
    xApp.start()
    # Note: xApp will unsubscribe all active subscriptions at exit
