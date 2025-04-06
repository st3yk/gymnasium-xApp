#!/bin/env bash
set -x
echo "Adding route from the host to gNB and UEs via core"
sudo ip ro add 10.45.0.0/16 via 10.53.1.2
echo "test gNB ping"
ping 10.45.1.1 -c 4
echo "Adding route from from UEs to the host via core"
for i in {1..2}; do
    ip=$((i + 1))
    sudo ip netns exec ue${i} ip route add default via 10.45.1.1 dev tun_srsue
    ping 10.45.1.${ip} -c 4
done
