# Data Files

### Log_Files
**Filename format**:

`[trial_number]_t[timeout_value]_rssi[rssi_cutoff]`

**trial_number** - The trial number. Just the trial ID.

**timeout_value** - Time before a device is forgotten
*e.g. timeout_value=60 means that if the device was seen in the last 59 seconds, it is counted. Otherwise it is not*

**rssi_cutoff** - Maximum signal strength permitted. 
*e.g. rssi_cutoff=60 means that a signal strength of 45 will be counted, a value of 70 will not*

### CSV Files

*Still working on completion*
