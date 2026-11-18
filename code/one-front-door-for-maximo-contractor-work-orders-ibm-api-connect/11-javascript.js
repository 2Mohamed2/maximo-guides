var mode = context.get('apiMode');
var STATE = { WAPPR: 'other', APPR: 'assigned', WSCH: 'assigned', INPRG: 'in_progress',
              COMP: 'done', CLOSE: 'done', CAN: 'other', WMATL: 'in_progress' };

function pub(m) {
  return { number: m.wonum, title: m.description || '',
           state: STATE[m.status] || 'other', priority: m.wopriority,
           site: m.siteid, location: m.location, asset: m.assetnum,
           type: m.worktype, dueBy: m.targcompdate };
}
function answer(code, reason, body) {
  context.set('message.status.code', code);
  context.set('message.status.reason', reason);
  context.message.header.set('Content-Type', 'application/json');
  context.message.body.write(body);
}

context.message.body.readAsJSON(function (err, json) {
  var status = context.get('message.status.code');
  if (err || status >= 400 || (json && json.Error)) {
    console.error('maximo said ' + status + ': ' + JSON.stringify(json));
    if (mode === 'complete' && json && json.Error) {
      var r = json.Error.reasonCode || '';
      if (r === 'NOTFOUND') return answer(404, 'Not Found', { error: 'not_found' });
      if (r === 'BADINPUT') return answer(400, 'Bad Request', { error: 'bad_input' });
      return answer(409, 'Conflict', { error: 'not_allowed', detail: json.Error.message });
    }
    return answer(502, 'Bad Gateway', { error: 'upstream_error' });
  }
  if (mode === 'list') {
    var items = (json.member || []).map(pub);
    return answer(200, 'OK', { items: items, count: items.length });
  }
  if (mode === 'one') {
    var m = (json.member || [])[0];
    return m ? answer(200, 'OK', pub(m)) : answer(404, 'Not Found', { error: 'not_found' });
  }
  return answer(200, 'OK', json);   // completion: the script already speaks the public shape
});
