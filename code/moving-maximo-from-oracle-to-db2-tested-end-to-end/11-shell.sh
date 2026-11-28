#!/bin/sh
# unlcvt.sh - run IBM's Unlcvt utility (psdi.configure.Unlcvt), which ships in Manage but has no launcher.
# Created by Mohamed Chihaoui.
#
# Put this file in <SMP>/maximo/tools/maximo/internal next to IBM's cleandatabase.sh (same pattern),
# point maximo.properties at the SOURCE database, stop every Maximo server, then run it from that folder:
#
#   cd <SMP>/maximo/tools/maximo/internal
#   ./unlcvt.sh -x3          # -x1 Oracle, -x2 SQL Server, -x3 Db2; no -x = same platform as the source
#
# Output: Unlcvt.db2 in the same folder (Unlcvt.ora / Unlcvt.sqs for the other platforms).
# Other flags read by the class: -m<n> split the output every n lines, -b alternative output format.
pathToScript=`dirname $0`
cd "$pathToScript"
. ./commonEnv.sh
../../java/jre/bin/java -Xmx6g -classpath ..:../classes:$MAXIMO_CLASSPATH psdi.configure.Unlcvt "$@"
exit $?
