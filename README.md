# gymnasium xApp
## Prerequisites
This repository includes custom xApp, Docker image and scripts for generating traffic.<br>
To use it, three repositories are needed:
 - [srsRAN\_Project](https://github.com/srsran/srsRAN_Project), commit: 9d5dd742a70e82c0813c34f57982f9507f1b6d5d
 - [srsRAN\_4G](https://github.com/srsran/srsRAN_4G), commit: ec29b0c1ff79cebcbe66caa6d6b90778261c42b8
 - [oran-sc-ric](https://github.com/srsran/oran-sc-ric), commit: 1356ee99cec9489acf8906768a7a8c927b07597d
To install, go through the provided tutorials:
 - [srsRAN gNB with srsUE](https://docs.srsran.com/projects/project/en/latest/tutorials/source/srsUE/source/index.html)
 - [O-RAN NearRT-RIC and xApp](https://docs.srsran.com/projects/project/en/latest/tutorials/source/near-rt-ric/source/index.html)

## Patches
This repository contains patches for two repositories: srsRAN\_Project and oran-sc-ric.
They are available in the patches directory.<br>
Changes for srsRAN\_Project include support for reading mcs and number of not ok packets as KPMs.
Please apply the patch before building.<br>
Change for oran-sc-ric is an xApp docker image switch. Please make sure to first build the original one, as the one from gymnasium-xApp is based on it.
## Running 5G network
Before running, please ensure that the config files are copied from the gymnasium-xApp repo, and the patches are applied.<br>
To connect 3 UEs, these steps must be performed in order:
 - start 5G core in srsRAN\_Project/docker:  $ docker compose up 5gc
 - start nearRT ric in oran-sc-ric:  $ docker compose up
 - start gNB in srsRAN\_Project/build/apps/gnb:  $ sudo ./gnb -c gnb\_zmq.yaml e2 --addr="10.0.2.10" --bind\_addr="10.0.2.1"
 - start all 3 UEs in srsRAN\_4G/srsRAN\_4G/build/srsue/src:  $ sudo ip netns add ue1; sudo ./srsue 5ue1.conf
 - start GNU-Radio Companion:  $ sudo gnuradio-companion multi\_ue\_scenario.grc

Then, to generate traffic, please use: scripts/add\_routes\_downlink.sh, and then scripts/traffic.py
## Running xApp
Once the docker image is changed, you can log onto it and run the xApp
```console
$ docker exec -ti python_xapp_runner bash
root@python_xapp_runner:/opt/xApps# ./my_xapp.py
1744982543159 21/RMR [INFO] ric message routing library on SI95 p=4560 mv=3 flg=00 id=a (f447e29 4.9.4 built: Dec 13 2023)
Subscribe to E2 node ID: gnbd_001_001_00019b_0, RAN func: e2sm_kpm, Report Style: 4, metrics: ['DRB.UEThpDl', 'RRU.PrbUsedDl', 'NokDl', 'McsDl']
Successfully subscribed with Subscription ID:  2vu6K85SD7zQRRqpZZQR2DLKAkX
```

