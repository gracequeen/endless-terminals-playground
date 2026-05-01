Traffic from our ML inference service in the 10.200.0.0/16 subnet is supposed to reach the model registry on port 5000, but it's timing out. The weird thing is the firewall rules look fine — I added an ACCEPT for that exact subnet and port in the INPUT chain. Checked iptables -L and I can see the rule sitting there. But packets are still getting dropped according to the logs. tcpdump on the registry box shows nothing arriving at all, so it's definitely being filtered somewhere on this gateway at /home/user/firewall.

The gateway does NAT and forwarding between the inference net (eth1, 10.200.0.0/16) and the registry net (eth2, 10.100.0.0/16). Registry is at 10.100.0.42:5000. I'm pretty sure it's just a rule ordering thing or maybe I put it in the wrong chain? But I've been staring at this for an hour and I don't see it.

Need the inference boxes to actually reach the registry. Rules are in /home/user/firewall/rules.sh.
