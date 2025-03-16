# gymnasium xApp
## Running 5G network
To connect 3 UEs, these steps must be performed in order:
 - start 5G core in srsRAN\_Project/docker:  $ docker compose up 5gc
 - start nearRT ric in oran-sc-ric:  $ docker compose up
 - start gNB in srsRAN\_Project/build/apps/gnb:  $ sudo ./gnb -c 5multi\_gnb\_zmq.yaml e2 --addr="10.0.2.10" --bind\_addr="10.0.2.1"
 - start all 3 UEs in srsRAN\_4G/srsRAN\_4G/build/srsue/src:  $ sudo ip netns add ue1 && ./srsue 5ue1.conf
 - start GNU-Radio Companion:  $ sudo gnuradio-companion multi\_ue\_scenario.grc

Then, to generate traffic, please use: scripts/traffic.py
