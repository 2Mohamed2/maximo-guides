-- first the rows (one per room), all with the same job number
INSERT INTO S_TRISPACE (DC_JOB_NUMBER, DC_CID, DC_SEQUENCE_ID, DC_STATE, DC_ACTION,
                        DC_PATH, DC_GUI_NAME, TRIIDTX, TRINAMETX, TRIAREANU)
VALUES (5001, 1, 1, <state: new>, <action: insert>,
        '\Locations\Offices\North America\Administration Building (BIM)\L1',
        'triSpace', 'L1_102', 'L1_102', 246.64);

-- then, last, the job row that says "ready"
INSERT INTO DC_JOB (JOB_NUMBER, JOB_NAME, JOB_TYPE, BO_NAME, STATE, …)
VALUES (5001, 'Weekly spaces', <type>, 'triSpace', <state: new>, …);
