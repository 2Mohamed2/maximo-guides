for m in 0101 0102 0103; do
  send "{\"meter\":\"MTR-4200-$m\",\"station\":\"4200-JCS-031500\",\"office\":\"2201\",\"alarm\":\"Last Gasp\",\"severity\":\"critical\",\"state\":\"cleared\"}"
  sleep 2
done
