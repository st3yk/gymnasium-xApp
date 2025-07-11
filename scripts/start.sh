#!/usr/bin/env bash
SESSION="srsRAN"
DIR="/home/ts"

tmux new-session -d -s $SESSION -n 5gc
# Add UE namespaces
sudo ip netns add ue1 && sudo ip netns add ue2

# Window 0: Start 5GC
tmux send-keys -t $SESSION:0 "cd ${DIR}/srsRAN_Project/docker && docker compose down && docker compose up 5gc" C-m

# Window 1: Start nearRT-RIC
tmux new-window -t $SESSION -n ric
tmux send-keys -t $SESSION:1 "cd ${DIR}/oran-sc-ric && docker compose down && docker compose up" C-m

# Window 2: Start gNB
sleep 5
tmux new-window -t $SESSION -n gnb
tmux send-keys -t $SESSION:2 "cd ${DIR}/srsRAN_Project/build/apps/gnb && sudo gdb --args ./gnb -c gnb_zmq.yaml e2 --addr='10.0.2.10' --bind_addr='10.0.2.1'" C-m

# Window 3: Start UE1
tmux new-window -t $SESSION -n ue1
tmux send-keys -t $SESSION:3 "cd ${DIR}/srsRAN_4G/build/srsue/src && sudo ./srsue ue1_zmq.conf" C-m

# Window 4: Start UE2
tmux new-window -t $SESSION -n ue2
tmux send-keys -t $SESSION:4 "cd ${DIR}/srsRAN_4G/build/srsue/src && sudo ./srsue ue2_zmq.conf" C-m

# Window 5: Start GNU Radio Companion
sleep 5
tmux new-window -t $SESSION -n grc
tmux send-keys -t $SESSION:5 "QT_QPA_PLATFORM=offscreen python3 ${DIR}/gymnasium-xApp/srsran/multi_ue_scenario.py" C-m

# Window 6: Routing test
sleep 5
tmux new-window -t $SESSION -n test
tmux send-keys -t $SESSION:6 "${DIR}/gymnasium-xApp/scripts/add_routes_downlink.sh" C-m

# Attach to session
tmux attach-session -t $SESSION
