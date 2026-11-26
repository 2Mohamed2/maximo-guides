cp Unlcvt.db2 <SMP>/maximo/tools/maximo/en/Unlcvt.db2
cd <SMP>/maximo/tools/maximo
# maximo.properties now points at the TARGET Db2 database
./maxinst.sh -e -iUnlcvt -tMAXDATA -sMAXINDEX
