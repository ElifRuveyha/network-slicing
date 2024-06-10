#!/bin/sh

#management slice 20% bandwidth
echo '-------- Deactivating 3. Development Slice -------'
echo '----------------------h1 h6-----------------------'

#s1 h6
sudo ovs-ofctl add-flow s1 ip,priority=65500,nw_src=10.0.0.1,nw_dst=10.0.0.6,idle_timeout=0,actions=drop

#s3 h6
sudo ovs-ofctl add-flow s3 ip,priority=65500,nw_src=10.0.0.6,nw_dst=10.0.0.1,idle_timeout=0,actions=drop
