# Data Files

## Log Files
Located in `Log_files`

**Filename format**:

`[trial_number]_t[timeout_value]_rssi[rssi_cutoff]`

**trial_number** - The trial number. Just the trial ID.

**timeout_value** - Time before a device is forgotten
*e.g. timeout_value=60 means that if the device was seen in the last 59 seconds, it is counted. Otherwise it is not*

**rssi_cutoff** - Maximum signal strength permitted. 
*e.g. rssi_cutoff=60 means that a signal strength of 45 will be counted, a value of 70 will not*

## CSV Files

Located in `csv` folder.

###No RSSI filtering
The same data is used in thw following two files. The difference being whether the devices are broken up by manufacturer.
#####rssi_NOrssi_man_breakdown
This data was gathered without any RSSI filtering. However the devices are broken down by manufacturer. 

#####rssi_NOrssi_total
This data was gathered without any RSSI filtering. The total number of devices located is listed, the manufacturers aren't listed.
###RSSI filtering
The same data is used in thw following two files. The difference being whether the devices are broken up by manufacturer.
#####rssi_rssi_man_breakdown
This data was gathered **with**  RSSI filtering. And the max rssi value (i.e. weakest signal strength) is a column. Further, the devices are broken down into manufacturers. 


#####rssi_rssi_total
This data was gathered **with**  RSSI filtering. And the max rssi value (i.e. weakest signal strength) is a column. The total number of devices is listed.

## ARFF Files
Located in `arff`

These files are used by WEKA.
