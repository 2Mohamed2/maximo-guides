# 1. log in: the answer contains a UserToken
curl -k -X POST https://localhost:9443/smcfs/restapi/invoke/login \
  -H "Content-Type: application/json" \
  -d '{"LoginID": "admin", "Password": "********"}'

# 2. call any API with the token: here getOrderList for the Matrix demo enterprise
curl -k -X POST "https://localhost:9443/smcfs/restapi/invoke/getOrderList?_loginid=admin&_token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"DocumentType": "0001", "MaximumRecords": "3"}'
