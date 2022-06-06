#!/bin/bash

# check if argument is present
if [ -z "$1" ]; then
    echo "Missing folder."
    exit 
fi

# If we're running haproxy results
# h_flag='false'
# while getopts 'h' flag; do
#     case "${flag}" in
#         f) h_flag='true' ;;
#     esac
# done


# Read contents into variables
folder=$1
clean="$1/clean.txt"
FO="$1/FO.txt"
FA="$1/FA.txt"
FAFO="$1/FAFO.txt"

function process() {
    # total read and timeout errors
    if grep "Socket" -q -F $1; then
        timeoutTemp=( $(grep "timeout" -F $1 | awk '{ print $10 }') )
        errTemp=( $(grep "errors" -F $1 | awk '{ print $6 }' | tr -d ',') )
        readErr=0
        timeout=0
        for ((i=0; i < 5; i++))
        do
            readErr=$(($readErr + ${errTemp[i]}))
            timeout=$(($timeout + ${timeoutTemp[i]}))
        done  
    else
        readErr=0
        timeout=0
    fi

    # averages
    requestTemp=( $(grep "requests" -F $1 | awk '{ print $1 }') )               # requests
    latAvgTemp=( $(grep "Latency" -F $1 | awk '{ print $2 }' | tr -d 'msuk') )   # latency avg
    latDevTemp=( $(grep "Latency" -F $1 | awk '{ print $3 }' | tr -d 'msuk') )   # latency deviation
    latMaxTemp=( $(grep "Latency" -F $1 | awk '{ print $4 }' | tr -d 'msuk') )   # latency max
    reqAvgTemp=( $(grep "Req/Sec" -F $1 | awk '{ print $2 }' | tr -d 'msuk') )   # request avg
    reqDevTemp=( $(grep "Req/Sec" -F $1 | awk '{ print $3 }' | tr -d 'msuk') )   # request deviation
    reqMaxTemp=( $(grep "Req/Sec" -F $1 | awk '{ print $4 }' | tr -d 'msuk') )   # request max
    requests=0
    latAvg=0
    latDev=0
    latMax=0
    reqAvg=0
    reqDev=0
    reqMax=0
    for ((i=0; i < 5; i++))
    do
        requests=$(($requests + ${requestTemp[i]}))
        latAvg=$( echo $latAvg + ${latAvgTemp[i]} | bc )
        latDev=$( echo $latDev + ${latDevTemp[i]} | bc )
        latMax=$( echo $latMax + ${latMaxTemp[i]} | bc )
        reqAvg=$( echo $reqAvg + ${reqAvgTemp[i]} | bc )
        reqDev=$( echo $reqDev + ${reqDevTemp[i]} | bc )
        reqMax=$( echo $reqMax + ${reqMaxTemp[i]} | bc )
    done
    requests=$(($requests / 5 ))
    readErr=$( printf '%.2f\n' "$(echo "scale=2 ;  $readErr / 5" | bc )" )
    timeout=$( printf '%.2f\n' "$(echo "scale=2 ;  $timeout / 5" | bc )" )
    latAvg=$( printf '%.2f\n' "$(echo "scale=2 ;  $latAvg / 5" | bc )" )
    latDev=$( printf '%.2f\n' "$(echo "scale=2 ;  $latDev / 5" | bc )" )
    latMax=$( printf '%.2f\n' "$(echo "scale=2 ;  $latMax / 5" | bc )" )
    reqAvg=$( printf '%.2f\n' "$(echo "scale=2 ;  $reqAvg / 5" | bc )" )
    reqDev=$( printf '%.2f\n' "$(echo "scale=2 ;  $reqDev / 5" | bc )" )
    reqMax=$( printf '%.2f\n' "$(echo "scale=2 ;  $reqMax / 5" | bc )" )

    # If haproxy failures are expected
    # if h_flag=='true' && grep "Non" -q -F $1; then
    #     xxError=0
    #     xxErrorTemp=( $(grep "Non" -F $1 | awk '{ print $5 }') )
    #     for ((i=0; i < 5; i++))
    #     do
    #         xxError=$(($xxError + ${xxErrorTemp[i]}))
    #     done
    #     xxError=$(($xxError / 5 ))
    # else
    #     xxError=0
    # fi

    echo $2,$latAvg,$latDev,$latMax,$reqAvg,$reqDev,$reqMax,$requests,$readErr,$timeout #,$xxError
}

# Create file
func_result="$(process $clean 1)"
func_result2="$(process $FO 2)"
func_result3="$(process $FA 3)"
func_result4="$(process $FAFO 4)"

echo "id,latencyAvg,latencyDev,latencyMax,reqAvg,reqDev,reqMax,requests,errRead,errTimeout" > ./$folder/output.csv
echo $func_result >> ./$folder/output.csv
echo $func_result2 >> ./$folder/output.csv
echo $func_result3 >> ./$folder/output.csv
echo $func_result4 >> ./$folder/output.csv
