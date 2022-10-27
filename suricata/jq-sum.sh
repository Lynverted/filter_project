#!/bin/bash

# jq -s 'map({ItemId: .alert.signature_id, Item: .alert.signature})
# | group_by(.ItemId)
# | map({ItemId: .[0].ItemId, Count: length, Item: .[0].Item })
# | .[]' ./log/suri2/eve.json

# Read JSON entries and count alerts associated with signature IDs
suri1=$(jq -s 'map({ItemId: .alert.signature_id, Item: .alert.signature})
| group_by(.ItemId)
| map({ItemId: .[0].ItemId, Count: length, Item: .[0].Item })
| .[]' ./log/suri1/eve.json)

suri2=$(jq -s 'map({ItemId: .alert.signature_id, Item: .alert.signature})
| group_by(.ItemId)
| map({ItemId: .[0].ItemId, Count: length, Item: .[0].Item })
| .[]' ./log/suri2/eve.json)


# Convert output to array | suri 1
output=$(jq -r '.Count' <<< "$suri1" | tail -n+2)
array=($output)
echo "Suricata 1:"
echo "  Total signatures: ${#array[@]}"

# Sum the alerts
for i in ${array[@]}
do
    let tot1+=$i
done
echo "  Total alerts: $tot1"

# Convert output to array | suri 2 
output2=$(jq -r '.Count' <<< "$suri2" | tail -n+2)
array2=($output2)
echo -e "\nSuricata 2:"
echo "  Total signatures: ${#array2[@]}"

# Sum the alerts
for i in ${array2[@]}
do
    let tot2+=$i
done
echo "  Total alerts: $tot2"