cp Unlcvt.db2 <SMP>/maximo/tools/maximo/en/Unlcvt.db2
cd <SMP>/maximo/tools/maximo
# maximo.properties -> the TARGET Db2 database
./maxinst.sh -e -iUnlcvt -tMAXDATA -sMAXINDEX
# BMXAA6820I - Maxinst completed without errors.   (1 h 20 min)
