person = {"personid": "AHADDAD", "firstname": w["firstName"], "lastname": w["lastName"],
          "title": w["jobTitle"], "department": w["department"], "supervisor": w["manager"],
          "location": w["workLocation"], "locationsite": "BEDFORD", "status": "ACTIVE",
          "email": [{"emailaddress": w["email"], "isprimary": True, "type": "WORK"}]}
mx.create("mxapiperson", person)      # POST /maximo/api/os/mxapiperson
