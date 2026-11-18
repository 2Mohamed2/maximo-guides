const API = '/html/en/default/rest/LocationReader';
async function get(params, callEl) {
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(API + '?' + qs, {credentials:'same-origin'});
  const j = await r.json();
  $(callEl).textContent = 'GET ' + API + '?' + qs + '  →  HTTP ' + r.status + ', ' + j.ms + ' ms';
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
}
