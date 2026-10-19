/* ATLAS HUB mini runtime
 * Renders a page template ({{holes}}, <template data-for>, <template data-if>) from a
 * component's renderVals(), patches the live DOM in place on every setState, and wires
 * on* handlers through delegated listeners. No dependencies. */
(function () {
  'use strict';

  function DCLogic(props) { this.props = props || {}; this.state = {}; }
  DCLogic.prototype.setState = function (patch) {
    var s = this;
    s.state = Object.assign({}, s.state, typeof patch === 'function' ? patch(s.state) : patch);
    if (s.__mounted && !s.__queued) {
      s.__queued = true;
      Promise.resolve().then(function () { s.__queued = false; s.__render(); });
    }
  };
  window.DCLogic = DCLogic;

  var HOLE = /\{\{([^}]+)\}\}/g;
  var EVENT_MAP = { onClick: 'click', onSubmit: 'submit', onPointerDown: 'pointerdown', onPointerMove: 'pointermove', onPointerUp: 'pointerup', onPointerLeave: 'pointerleave', onInput: 'input', onKeyDown: 'keydown', onFocus: 'focus', onBlur: 'blur' };

  function lookup(scope, path) {
    var parts = path.trim().split('.'), v = scope;
    for (var i = 0; i < parts.length; i++) { if (v == null) return undefined; v = v[parts[i]]; }
    return v;
  }
  function str(v) { return v == null || typeof v === 'function' || typeof v === 'object' ? '' : String(v); }
  function single(value) { var m = /^\s*\{\{([^}]+)\}\}\s*$/.exec(value); return m ? m[1] : null; }

  function build(src, scope, out) {
    var kids = src.childNodes;
    for (var i = 0; i < kids.length; i++) {
      var n = kids[i];
      if (n.nodeType === 3) { out.appendChild(document.createTextNode(n.nodeValue.indexOf('{{') < 0 ? n.nodeValue : n.nodeValue.replace(HOLE, function (_, p) { return str(lookup(scope, p)); }))); continue; }
      if (n.nodeType !== 1) continue;
      if (n.tagName === 'TEMPLATE' && n.hasAttribute('data-for')) {
        var list = lookup(scope, single(n.getAttribute('data-for')) || '') || [], as = n.getAttribute('data-as');
        for (var j = 0; j < list.length; j++) { var sc = Object.create(scope); sc[as] = list[j]; build(n.content, sc, out); }
        continue;
      }
      if (n.tagName === 'TEMPLATE' && n.hasAttribute('data-if')) {
        var v = lookup(scope, single(n.getAttribute('data-if')) || '');
        if (v && v !== 'false') build(n.content, scope, out);
        continue;
      }
      var isSvg = n.namespaceURI === 'http://www.w3.org/2000/svg';
      var el = isSvg ? document.createElementNS('http://www.w3.org/2000/svg', n.localName) : document.createElement(n.localName);
      var attrs = n.attributes;
      for (var a = 0; a < attrs.length; a++) {
        var key = attrs[a].name, val = attrs[a].value;
        var jsName = attrs[a].localName;
        var evName = EVENT_MAP[toCamel(jsName)];
        if (/^on/i.test(jsName)) {
          var fn = lookup(scope, single(val) || '');
          if (typeof fn === 'function') {
            var type = evName || (toCamel(jsName) === 'onChange' ? (n.tagName === 'SELECT' || (n.getAttribute('type') || '') === 'checkbox' ? 'change' : 'input') : null);
            if (type) { (el.__h || (el.__h = {}))[type] = fn; }
          }
          continue;
        }
        if (jsName === 'ref') { var rf = lookup(scope, single(val) || ''); if (typeof rf === 'function') el.__ref = rf; continue; }
        if (jsName.indexOf('hint-') === 0) continue;
        var out2 = val.indexOf('{{') < 0 ? val : val.replace(HOLE, function (_, p) { return str(lookup(scope, p)); });
        if (jsName === 'value') el.__value = out2;
        try { el.setAttribute(key, out2); } catch (e) {}
      }
      build(n.tagName === 'TEMPLATE' ? n.content : n, scope, el);
      out.appendChild(el);
    }
  }
  function toCamel(attr) {
    // template attributes are lower-cased by the HTML parser: map back to known handler names
    var m = { onclick: 'onClick', onchange: 'onChange', onsubmit: 'onSubmit', onpointerdown: 'onPointerDown', onpointermove: 'onPointerMove', onpointerup: 'onPointerUp', onpointerleave: 'onPointerLeave', oninput: 'onInput', onkeydown: 'onKeyDown', onfocus: 'onFocus', onblur: 'onBlur' };
    return m[attr.toLowerCase()] || attr;
  }

  function patch(live, fresh, refs) {
    var lk = live.childNodes, fk = Array.prototype.slice.call(fresh.childNodes), i;
    var n = fk.length;
    for (i = 0; i < n; i++) {
      var f = fk[i], l = lk[i];
      if (!l) { live.appendChild(adopt(f, refs)); continue; }
      if (l.nodeType !== f.nodeType || (l.nodeType === 1 && l.tagName !== f.tagName)) { live.replaceChild(adopt(f, refs), l); continue; }
      if (l.nodeType === 3) { if (l.nodeValue !== f.nodeValue) l.nodeValue = f.nodeValue; continue; }
      syncAttrs(l, f);
      l.__h = f.__h;
      patch(l, f, refs);
      if (f.__value !== undefined && /^(INPUT|TEXTAREA|SELECT)$/.test(l.tagName) && l.value !== f.__value) l.value = f.__value;
      if (f.__ref) refs.push([f.__ref, l]);
    }
    while (lk.length > n) live.removeChild(live.lastChild);
  }
  function adopt(f, refs) {
    // move a freshly built subtree into the live DOM, keeping handler/ref/value markers
    var stack = [f];
    while (stack.length) {
      var x = stack.pop();
      if (x.nodeType === 1) {
        if (x.__ref) refs.push([x.__ref, x]);
        if (x.__value !== undefined && /^(INPUT|TEXTAREA|SELECT)$/.test(x.tagName)) refs.push([setVal(x.__value), x]);
        for (var c = 0; c < x.childNodes.length; c++) stack.push(x.childNodes[c]);
      }
    }
    return f;
  }
  function setVal(v) { return function (el) { if (el.value !== v) el.value = v; }; }
  function syncAttrs(l, f) {
    var la = l.attributes, fa = f.attributes, i;
    for (i = la.length - 1; i >= 0; i--) { var nm = la[i].name; if (!f.hasAttribute(nm)) l.removeAttribute(nm); }
    for (i = 0; i < fa.length; i++) { if (l.getAttribute(fa[i].name) !== fa[i].value) l.setAttribute(fa[i].name, fa[i].value); }
  }

  function delegate(root) {
    ['click', 'submit', 'input', 'change', 'pointerdown', 'pointermove', 'pointerup', 'keydown'].forEach(function (type) {
      root.addEventListener(type, function (e) {
        var el = e.target;
        while (el && el !== root.parentNode) {
          if (el.__h && el.__h[type]) {
            if (type === 'submit') e.preventDefault();
            var r = el.__h[type].call(el, e);
            if (type === 'click' && el.tagName === 'A' && r === false) e.preventDefault();
            return;
          }
          el = el.parentNode;
        }
      });
    });
    root.addEventListener('pointerleave', function (e) { var el = e.target; if (el && el.__h && el.__h.pointerleave) el.__h.pointerleave.call(el, e); }, true);
  }

  window.mountAtlas = function (Component) {
    var tplSrc = document.getElementById('tpl').textContent;
    var tpl = document.createElement('template');
    tpl.innerHTML = tplSrc;
    var root = document.getElementById('app');
    delegate(root);
    var c = new Component({});
    c.__render = function () {
      var vals;
      try { vals = c.renderVals(); } catch (e) { console.error(e); return; }
      var frag = document.createElement('div');
      build(tpl.content, vals, frag);
      var refs = [];
      patch(root, frag, refs);
      refs.forEach(function (r) { try { r[0](r[1]); } catch (e) {} });
      if (window.__afterRender) { try { window.__afterRender(c); } catch (e) {} }
    };
    c.__render();
    c.__mounted = true;
    if (c.componentDidMount) c.componentDidMount();
    window.addEventListener('pagehide', function () { if (c.componentWillUnmount) c.componentWillUnmount(); });
    window.__atlas = c;
  };
})();
