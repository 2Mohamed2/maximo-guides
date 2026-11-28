python dual_run.py --ora-shell 'ssh oracle-host bash -s' --db2-shell 'ssh db2inst1@db2-host bash -s' \
                   --ora-conn 'maximo/<password>@//<host>:1521/<service>' --out before.csv
python dual_run.py ... --rewrites db2_rewrites.csv --out after.csv
