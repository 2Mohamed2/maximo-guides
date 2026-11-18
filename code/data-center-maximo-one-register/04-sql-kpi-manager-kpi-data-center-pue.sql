Select : measurementvalue
From   : measurement
Where  : siteid = 'NORTH' and assetnum = 'DC-ENERGY' and metername = 'PUE'
         and measuredate = (select max(measuredate) from measurement
                            where siteid = 'NORTH' and assetnum = 'DC-ENERGY' and metername = 'PUE')

Target 1.4   Caution 1.5   Alert 1.7   (lower is better)
