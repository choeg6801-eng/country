/* ATLAS HUB shared tips board client (Supabase REST, no SDK).
 * Public publishable key only: the database allows anonymous users to READ visible posts, INSERT new posts
 * (length/link/abuse checks + 5 posts per 10 min in a database trigger) and REPORT a post (3 reports hide it).
 * Nothing else (no update/delete, no IP address readable). */
window.ATLAS_SHARED = (function () {
  'use strict';
  var API = 'https://vdqaqksvngecoakpbqvi.supabase.co/rest/v1';
  var KEY = 'sb_publishable_sU7_eGHyI1F2siIb7cZhHg_fUVAfz0V';
  var cache = {};
  function headers(extra) { var h = { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' }; for (var k in extra) h[k] = extra[k]; return h; }
  function rerender() { if (window.__atlas && window.__atlas.__render) window.__atlas.__render(); }
  function load(key) {
    var prev = cache[key];
    cache[key] = { status: 'loading', items: prev ? prev.items : [] };
    if (!window.fetch) { cache[key] = { status: 'error', items: [] }; return; }
    var q = '/atlas_posts?select=id,code,cat,body,nick,created_at&order=created_at.desc&limit=200' + (key === 'ALL' ? '' : '&code=eq.' + encodeURIComponent(key));
    fetch(API + q, { headers: headers({}) }).then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (j) { cache[key] = { status: 'ok', items: Array.isArray(j) ? j : [], t: Date.now() }; rerender(); },
            function () { cache[key] = { status: 'error', items: [] }; rerender(); });
  }
  function msgOf(j) {
    if (!j) return '등록하지 못했어요. 잠시 후 다시 시도해 주세요.';
    if (j.code === '23514') return '글은 5~300자, 별명은 20자까지 쓸 수 있어요.';
    if (j.code === 'P0001' && j.message) return j.message;
    return '등록하지 못했어요. 잠시 후 다시 시도해 주세요.';
  }
  return {
    get: function (code) { var key = code || 'ALL'; if (!cache[key]) load(key); return cache[key]; },
    refresh: function (code) { delete cache[code || 'ALL']; delete cache.ALL; rerender(); },
    post: function (p) {
      return fetch(API + '/atlas_posts', { method: 'POST', headers: headers({ Prefer: 'return=minimal' }), body: JSON.stringify({ code: p.code, cat: p.cat, body: p.body, nick: p.nick || '여행자' }) })
        .then(function (r) { if (r.ok) return true; return r.json().then(function (j) { throw new Error(msgOf(j)); }, function () { throw new Error(msgOf(null)); }); },
              function () { throw new Error('인터넷 연결을 확인해 주세요.'); });
    },
    report: function (id) {
      return fetch(API + '/rpc/atlas_report', { method: 'POST', headers: headers({}), body: JSON.stringify({ p_id: id }) })
        .then(function (r) { return r.ok ? r.json() : false; }, function () { return false; });
    },
    ago: function (iso) {
      var s = (Date.now() - Date.parse(iso)) / 1000;
      if (!(s >= 0)) return '';
      if (s < 60) return '방금'; if (s < 3600) return Math.floor(s / 60) + '분 전'; if (s < 86400) return Math.floor(s / 3600) + '시간 전';
      if (s < 86400 * 30) return Math.floor(s / 86400) + '일 전';
      var d = new Date(iso); return d.getFullYear() + '.' + (d.getMonth() + 1) + '.' + d.getDate();
    }
  };
})();
