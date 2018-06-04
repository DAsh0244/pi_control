#! /usr/bin/env bash
# diagnostics to check pi baseline performance figures
# lshw is a required command
# sudo apt-get install lshw
# ./get_diagnostic_info.sh
# take the outputted diagnostic_info.txt file and pass that back

outfile=diagnostic_info.txt

echo diagnostic information script V0.01: > "$outfile"

# get machine info
echo uname: >> "$outfile"
uname -a  >> "$outfile"

sed -i -e '$a\' "$outfile"

# read cpuinfo
echo  cpuinfo: >> "$outfile"
cat /proc/cpuinfo >> "$outfile"

sed -i -e '$a\' "$outfile"

# get cpu clockrate
echo cpu clock: >> "$outfile"
lshw -c cpu | grep capacity >> "$outfile"

sed -i -e '$a\' "$outfile"

# check i2c baudrate
echo i2c baud information: >> "$outfile"
sudo cat /sys/module/i2c_bcm2708/parameters/baudrate

sed -i -e '$a\' "$outfile"

# get full lshw dump
echo lshw full output: >> "$outfile"
lshw  >> "$outfile"

sed -i -e '$a\' "$outfile"
