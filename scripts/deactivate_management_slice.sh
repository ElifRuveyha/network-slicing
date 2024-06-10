#!/bin/sh

#management slice 30% bandwidth
echo '-------- Deactivating 2.Management Slice --------'
echo '-----------------------h5 h7---------------------'

#s3 h5

sudo ovs-ofctl add-flow s3 ip,priority=65500,nw_src=10.0.0.5,nw_dst=10.0.0.7,idle_timeout=0,actions=drop

#s4 h7

sudo ovs-ofctl add-flow s4 ip,priority=65500,nw_src=10.0.0.7,nw_dst=10.0.0.5,idle_timeout=0,actions=drop
