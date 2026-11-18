// build-query: decide the Maximo call from the public call.
// The vendor comes from the caller's consumer organization, never from the request.
var vendor = context.get('client.org.name') || '';
var verb   = context.get('request.verb');
var path   = context.get('request.path');          // e.g. /contractor/v1/workorders/1203/completion
var rest   = path.replace(/^.*\/workorders/, '');  // '', '/1203' or '/1203/completion'

// A named rejection goes to the ClientError catch, which keeps this status code
function fail(code, reason, msg) {
  context.reject('ClientError', msg);
  context.message.statusCode = code + ' ' + reason;
}

if (!/^[A-Z0-9]{1,12}$/.test(vendor.toUpperCase())) {
  fail(403, 'Forbidden', 'This application is not linked to a contractor.');
} else {
  vendor = vendor.toUpperCase();
  var SELECT = 'wonum,description,status,wopriority,siteid,location,assetnum,worktype,targcompdate';
  var parts  = rest.split('/').filter(function (p) { return p; });
  var number = parts[0] ? decodeURIComponent(parts[0]) : null;

  if (number !== null && !/^[A-Z0-9-]{1,25}$/.test(number)) {
    fail(400, 'Bad Request', 'Work order number may contain A-Z, 0-9 and - only.');
  } else if (verb === 'GET' && number === null) {
    // Statuses as shown in Maximo. Add your own synonyms here (for example "WAITCONTR").
    var filter = { open: ' and status in ["APPR","WSCH","INPRG","WMATL"]',
                   done: ' and status in ["COMP","CLOSE"]',
                   all:  '' };
    var q = (context.get('request.parameters.status.values') || ['open'])[0];
    var where = 'vendor="' + vendor + '"' + (filter[q] !== undefined ? filter[q] : filter.open);
    context.set('maximoPath', '/maximo/api/os/contrwo?lean=1&oslc.pageSize=100'
      + '&oslc.select=' + SELECT
      + '&oslc.where=' + encodeURIComponent(where)
      + '&oslc.orderBy=' + encodeURIComponent('+wopriority'));
    context.set('apiMode', 'list');
  } else if (verb === 'GET') {
    var w = 'wonum="' + number + '" and vendor="' + vendor + '"';
    context.set('maximoPath', '/maximo/api/os/contrwo?lean=1&oslc.select=' + SELECT
      + '&oslc.where=' + encodeURIComponent(w));
    context.set('apiMode', 'one');
  } else if (verb === 'POST' && parts[1] === 'completion') {
    context.message.body.readAsJSON(function (err, body) {
      if (err || !body || !body.note || !body.completedAt) {
        fail(400, 'Bad Request', 'completedAt and note are required.');
        return;
      }
      context.set('maximoPath', '/maximo/api/script/contractor_complete');
      context.message.header.set('x-contractor-vendor', vendor);
      context.message.header.set('Content-Type', 'application/json');
      context.message.body.write({ wonum: number, completedAt: String(body.completedAt).substring(0, 30),
                                   note: String(body.note).substring(0, 2000) });
      context.set('apiMode', 'complete');
    });
  } else {
    fail(404, 'Not Found', 'Unknown operation.');
  }
}
