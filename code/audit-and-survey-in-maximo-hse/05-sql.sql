select sum(linescore) as total, sum(linescore * plusgweightfactor) as weighted, sum(plusgmaxscore) as max_unweighted, sum(plusgmaxscore * plusgweightfactor) as max_weighted
from plusgaudline
where plusgauditid = 2
