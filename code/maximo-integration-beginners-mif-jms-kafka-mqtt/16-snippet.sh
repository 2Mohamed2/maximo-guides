$ oc logs -n mas-instdb2-monitor <latest wsp.g1... pod> | grep -i kmeans
KMeans, Entity: PUMP-001, Input: vibration, Windowsize: 12, Output: ['vibration_anomaly'], Overlap: 6, Inputsize: 30
KMeans failed with Could not form valid cluster separation. Please change n_clusters or change clustering method
