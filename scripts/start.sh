#!/usr/bin/env bash
# Run without sudo

DIR="/home/tymons/Repos/srsRAN/"

echo "Creating a tab with 5gc container..."
gnome-terminal --tab -- bash -c "cd ${DIR}/srsRAN_Project/docker && docker compose down && docker compose up 5gc; bash"
sleep 5 # wait for the 5gc to start

echo "Creating a tab with nearRT-RIC containers..."
gnome-terminal --tab -- bash -c "cd ${DIR}/oran-sc-ric && docker compose down && docker compose up; bash"
sleep 5 # wait for the nearRT-RIC to start

echo "Start gNB"
gnome-terminal --tab -- bash -c "cd ${DIR}/srsRAN_Project/build/apps/gnb && sudo ./gnb -c gnb_zmq.yaml e2 --addr='10.0.2.10' --bind_addr='10.0.2.1'; bash"

echo "Add network namespaces for the UEs"
gnome-terminal --tab -- bash -c "sudo ip netns add ue1 && sudo ip netns add ue2"

echo "Start UEs"
gnome-terminal --tab -- bash -c "cd ${DIR}/srsRAN_4G/build/srsue/src && sudo ./srsue ue1_zmq.conf; bash"
gnome-terminal --tab -- bash -c "cd ${DIR}/srsRAN_4G/build/srsue/src && sudo ./srsue ue2_zmq.conf; bash"
# gnome-terminal --tab -- bash -c "cd ${DIR}/srsRAN_4G/build/srsue/src && sudo ./srsue ue3_zmq.conf; bash"

echo "Start GNU Radio Companion"
gnome-terminal --tab -- bash -c "sudo gnuradio-companion ${DIR}/../gymnasium-xApp/srsran/multi_ue_scenario2.grc; bash"
