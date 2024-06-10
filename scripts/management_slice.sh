#!/bin/sh

#management slice 30% bandwidth
echo '--------------- 2.Management Slice --------------'
echo '-----------------------h5 h7---------------------'

#s2

sudo ovs-ofctl add-flow s2 ip,priority=65500,nw_src=10.0.0.5,nw_dst=10.0.0.7,idle_timeout=0,actions=normal
sudo ovs-ofctl add-flow s2 ip,priority=65500,nw_src=10.0.0.7,nw_dst=10.0.0.5,idle_timeout=0,actions=normal

#s3 h5

sudo ovs-ofctl add-flow s3 ip,priority=65500,nw_src=10.0.0.5,nw_dst=10.0.0.7,idle_timeout=0,actions=output:controller

#s4 h7

sudo ovs-ofctl add-flow s4 ip,priority=65500,nw_src=10.0.0.7,nw_dst=10.0.0.5,idle_timeout=0,actions=output:controller
