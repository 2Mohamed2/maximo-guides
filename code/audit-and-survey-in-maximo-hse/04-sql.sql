select linenum, section, sequence, yes, no, notapplicable, linescore, plusgmaxscore, plusgweightfactor, description
from plusgaudline
where plusgauditid = 2
order by linenum
