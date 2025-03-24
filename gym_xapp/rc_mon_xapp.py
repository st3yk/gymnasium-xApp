#!/usr/bin/env python3

import time
import datetime
import argparse
import signal
from lib.xAppBase import xAppBase
from lib.DummyAgent import DummyAgent


class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)
        self.agent = DummyAgent()
        self.prb_ratio_values = [1, 5, 10, 20]
        self.prev_state = None
        self.action = 2  # first action, init with a 10 PRB
        self.current_state = None
        self.train_counter = 0
        self.total_reward = 0
        self.epoch = 400
        self.ep_r = 0

    def extract_state(self, meas_data):
        # Extract metrics from the received e2sm_kpm
        # Return it in the form of the state for the RL agent
        for metric_name, value in meas_data["measData"].items():
            print(f"--Metric: {metric_name}, Value: {value}")

        # metrics come in a form of 1-element lists [[], [], ..., []]
        unpacked_state = [metric[0] if isinstance(metric, list) and len(metric) == 1 else 0 for metric in meas_data["measData"].values()]
        state = tuple(unpacked_state)
        print(f"Current state: {state}")
        return state

    def execute_action(self):
        # Perform RC action that was decided by the algorithm
        e2_node_id, ue_id = 'gnbd_001_001_00019b_0', 0 # TODO pass from args
        selected_prb_ratio = self.prb_ratio_values[self.action]
        print(f"Current action is {self.action}, setting slice level prb quota to {selected_prb_ratio}")
        self.e2sm_rc.control_slice_level_prb_quota(
            e2_node_id,
            ue_id,
            min_prb_ratio=1,
            max_prb_ratio=selected_prb_ratio,
            dedicated_prb_ratio=100,
            ack_request=1,
        )

    def my_subscription_callback(
        self, e2_agent_id, subscription_id, indication_hdr, indication_msg
    ):
        print(
            "\nRIC Indication Received from {} for Subscription ID: {}".format(
                e2_agent_id, subscription_id
            )
        )
        indication_hdr = self.e2sm_kpm.extract_hdr_info(indication_hdr)
        meas_data = self.e2sm_kpm.extract_meas_data(indication_msg)

        self.current_state = self.extract_state(meas_data)
        if self.prev_state is not None:
            reward = self.agent.calculate_reward(
                self.prev_state, self.action, self.current_state
            )
            self.agent.store_transition(
                self.prev_state, self.action, self.current_state, reward
            )
            self.action = self.agent.select_action(self.current_state)
            self.execute_action()
            self.agent.learn()

            self.epoch += 1
            self.ep_r += reward
            if self.epoch % 10 == 0 and self.epoch != 0:
                print(f"### episode #{self.epoch}, avg score: {ep_r / 10:.3f} ###")
                self.ep_r = 0
        self.prev_state = self.current_state

    # Mark the function as xApp start function using xAppBase.start_function decorator.
    # It is required to start the internal msg receive loop.
    # This can be treated as a training loop for a DRL algorithm
    @xAppBase.start_function
    def start(self, e2_node_id, metric_names):
        print(
            "Subscribe to E2 node ID: {}, RAN func: e2sm_kpm for metrics {}".format(
                e2_node_id, metrics
            )
        )
        report_period = 5000
        granul_period = 2
        self.e2sm_kpm.subscribe_report_service_style_1(
            e2_node_id,
            report_period,
            metric_names,
            granul_period,
            self.my_subscription_callback,
        )
        if self.ep_r == self.epoch:
            print("Finish")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="My example xApp")
    parser.add_argument("--config", type=str, default="", help="xApp config file path")
    parser.add_argument(
        "--http_server_port", type=int, default=8091, help="HTTP server listen port"
    )
    parser.add_argument("--rmr_port", type=int, default=4560, help="RMR port")
    parser.add_argument(
        "--e2_node_id", type=str, default="gnbd_001_001_00019b_0", help="E2 Node ID"
    )
    parser.add_argument("--ue_id", type=int, default=0, help="UE ID")
    parser.add_argument("--ran_func_id", type=int, default=2, help="RAN function ID")
    parser.add_argument(
        "--metrics",
        type=str,
        default="DRB.UEThpDl",
        help="Metrics name as comma-separated string",
    )

    args = parser.parse_args()
    config = args.config
    e2_node_id = (
        args.e2_node_id
    )  # TODO: get available E2 nodes from SubMgr, now the id has to be given.
    ran_func_id = (
        args.ran_func_id
    )  # TODO: get available E2 nodes from SubMgr, now the id has to be given.

    # There are also 3 metrics available via gNB, but absent in our setup:
    # DRB.AirIfDelayUl
    # DRB.RlcDelayUl
    # RACH.PreambleDedCell

    with open("metrics.lst", "r") as file:
        metrics = [line.strip() for line in file]

    # Create MyXapp.
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port)
    myXapp.e2sm_kpm.set_ran_func_id(ran_func_id)

    # Connect exit signals.
    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    # Start xApp.
    myXapp.start(e2_node_id, metrics)
    # Note: xApp will unsubscribe all active subscriptions at exit.
