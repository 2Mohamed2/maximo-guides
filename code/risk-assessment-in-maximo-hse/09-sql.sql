select status, convert(varchar(16), changedate, 120), changeby, cast(memo as varchar(80)) from plusgriskstatus where plusgriskassessid=101 order by changedate
