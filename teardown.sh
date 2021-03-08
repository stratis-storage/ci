#!/bin/bash
echo "Terminating test processes:"
ps -ef | egrep 'stratisd.sh|make|cargo|libstratis|PPID' | grep -v grep
ps aux | egrep 'stratisd.sh|make|cargo|libstratis|RSS' | grep -v grep
pkill 'stratisd.sh|make|cargo|libstratis'
pkill 'stratisd.sh|make|cargo|libstratis'
for j in $(ps aux | grep target/debug/stratisd\ --sim | grep -v grep | awk '{print $2}')
do 
	echo "Terminating target/debug/stratisd --sim process $j"
	kill $j
done
echo

# Wait for a few seconds for the I/O to finish.
sleep 4

lsblk -i
dmsetup info -c

# If the thin-pool devices are suspended, the next steps will fail.
# Therefore, resume them now.
# (If they're not suspended, nothing will happen.)
for j in $(dmsetup ls | grep thinpool-pool | awk {'print $1'})
do
	echo "Ensuring thin-pool device is not suspended"
	dmsetup resume $j
	echo
done

echo "Unmounting active stratis test mounts (if any):"
for j in $(grep stratis_testing /proc/mounts | awk {'print $2'})
do
	echo $j
	umount $j
done
echo

# Now tear down the remnant stratis component devices, top to bottom.
for i in thin-fs thinpool-pool flex-thinmeta flex-thindata flex-mdv physical-originsub stratis_test_ stratis-.*private-.*-crypt
do
	for j in $(dmsetup ls | grep $i | awk {'print $1'})
	do
		echo "Removing device:"
		dmsetup info -c $j
		dmsetup table $j
		dmsetup remove $j
		echo
	done
done

for testdevs in $(grep /dev /etc/stratis/test_config.json | tr -d \"\,)
do
	for wipetgt in $(blkid -p $testdevs | grep stratis | awk '{print $1}' | tr -d \:)
	do
		echo "Wiping signature on $wipetgt:"
		wipefs -a $wipetgt
	done
done

