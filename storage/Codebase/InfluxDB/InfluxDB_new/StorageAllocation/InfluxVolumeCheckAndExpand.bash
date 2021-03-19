#! /bin/bash

# #############################################################
# Description
#
# Author :Indranil Ghosh
#
# Date :
#
# Rev :
#
###############################################################

#Commands
DF=/bin/df
AWK=/usr/bin/awk
GREP=grep
KUBECTL=/usr/bin/kubectl
DATE=/bin/date
ECHO=/bin/echo
CD=/bin/cd
SED=/bin/sed
CAT=/bin/cat

#File paths

MOUNT_POINT=/var/lib/influxdb
PVCPATH=/home/user/heketi/extras/kubernetes

Expend_vol() {
	extra_space=$1
	cd $PVCPATH
	current_size=$($CAT persistent-volume-claim.yaml | $GREP storage: | $AWK '{print $2}')
	$CAT $PVCPATH/persistent-volume-claim.yaml | $SED 's/'$current_size'/'$extra_space'/' >persistent-volume-claim-$extra_space.yaml
	$KUBECTL apply -f persistent-volume-claim-$extra_space.yaml
	return $?
}

Influx_db_fileystem_uses() {

	influxdb_container_name=$( $KUBECTL get pods | $GREP -w influxdbnew | $AWK '{print $1}')
	glustervol_Uses=$($KUBECTL exec -it $influxdb_container_name -- $DF -h | $GREP $MOUNT_POINT | $AWK '{print $5}' | $SED 's/%//')
	if [ $glustervol_Uses -ge 3 ];then
		extra_space=6Gi
		$ECHO "influxdb volume uses from Glusterfs is more than 80%.. extending with $extra_space "
		Expend_vol $extra_space
		if [ $? == 0 ];then
		$ECHO "-Influxdb volume has been expended with $extra_space"
		$ECHO "Bye" 
		exit 0
		fi
	else
	$ECHO "-${glustervol_Uses}% Influxdb utilization is okay - no need add extra space"
	fi
}


get_data_csv_file(){

	username=$($CAT ../etc/influxbd_script.cfg | $AWK '/username:/ {print $2}')
	password=$(CAT ../etc/influxdb_script.cfg | $AWk '/password:/ {print $2}')
	servername=$($CAT ../etc/influxdb_script.cfg | $AWk '/password:/ {print $2}')
	sshpass -p ${password} $username@$servername:/tmp .
	if [ $? == 0 ];then
		$ECHO "-data.csv file is copied successfully .."
	fi

}

get_influxdb_pod_statu(){
        while true;do
		podstatus=$(kubectl get pods | grep influxdbnew | awk '{print $3}')
		if [ $podstatus == "Running" ];then
       		 	echo "Influxdbnew pod is running"
	                break
			if [ ! -z $START ];then
				echo "Influxdbnew pod is terminited"
				END=$(date +%s)
				echo "Infuldb is started with below time differ ...."
				echo $((END-START)) | awk '{print int($1/60)":"int($1%60)}'
			fi
		else 
				START=$(date +%s)
		fi
        done

}

Influx_db_fileystem_uses
get_influxdb_pod_statu
