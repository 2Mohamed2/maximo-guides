python find_tsql.py extract > extract.sql
sqlcmd -C -S <host> -U maximo -P <password> -d MAXDB -y 0 -s "~" -i extract.sql -o extract.txt
python find_tsql.py classify extract.txt > findings.csv
