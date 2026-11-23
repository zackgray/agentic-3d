/* The viewer, the header and the strip of items. */

J.$ = function (id) { return document.getElementById(id); };

J.toast = function (msg) {
  var t = J.$('toast');
  t.textContent = msg;
  t.className = 'on';
  clearTimeout(J.toastTimer);
  J.toastTimer = setTimeout(function () { t.className = ''; }, 3500);
};

J.render = function () {
  J.renderHeader();
  J.renderViewer();
  J.renderPanel();
  J.renderStrip();
};

/* progress is a count and nothing else */
J.renderHeader = function () {
  var pending = J.unexported(), saved = J.$('saved');
  J.$('title').textContent = J.D.title;
  J.$('progress').textContent = 'Scored ' + J.countGraded() + ' of ' + J.list().length;
  saved.textContent = J.saveFailed ? 'Browser could not save: save the file now (E)'
    : pending ? pending + ' changes not yet saved to a file' : 'All changes saved to a file';
  saved.className = J.saveFailed || pending >= 25 ? 'warn' : '';
  document.title = (pending ? '* ' : '') + 'Judging';
};

J.VIEWS = { item: 'im-item', ref: 'im-ref', photo: 'im-photo' };

J.imageFor = function (view, it) {
  if (view === 'ref') return it.ref;
  if (view === 'photo') return it.photo;
  return it.image;
};

J.renderViewer = function () {
  var it = J.curItem();
  if (!it) return;
  Object.keys(J.VIEWS).forEach(function (v) {
    var src = J.imageFor(v, it), img = J.$(J.VIEWS[v]);
    if (src && img.getAttribute('src') !== src) img.setAttribute('src', src);
    if (!src) img.removeAttribute('src');
  });
  J.showView();
};

J.showView = function () {
  var it = J.curItem();
  if (!it) return;
  var view = J.ui.view, has = !!J.imageFor(view, it);
  Object.keys(J.VIEWS).forEach(function (v) { J.$(J.VIEWS[v]).className = v === view && has ? 'on' : ''; });
  J.$('stage').className = (J.ui.actual ? 'actual' : '') + (has ? '' : ' empty');
  J.$('caption').innerHTML = J.caption(view);
};

J.caption = function (view) {
  var where = 'Item ' + (J.ui.cur + 1) + ' of ' + J.list().length;
  var size = J.ui.actual ? ' &middot; 100% (Z to fit)' : ' &middot; fitted (Z for 100%)';
  if (view === 'ref') return '<b>Reference model</b> (hold R), same four views. Showing: ' + where + size;
  if (view === 'photo') return '<b>Product photo</b> (hold P), what the agent saw. Showing: ' + where + size;
  return '<b>' + where + '</b>: front, side / three-quarter, top' + size;
};

J.renderStrip = function () {
  var strip = J.$('strip'), list = J.list();
  if (!strip.children.length) {
    list.forEach(function (it, i) {
      var th = document.createElement('div');
      th.className = 'th';
      th.innerHTML = '<img loading="lazy" alt="" src="' + it.image + '"><span class="n">' + (i + 1) +
                     '</span><span class="sc"></span>';
      th.addEventListener('click', function () { J.goto(i); });
      strip.appendChild(th);
    });
  }
  for (var i = 0; i < strip.children.length; i++) {
    var th = strip.children[i], g = J.gradeOf(list[i].id);
    th.className = 'th' + (i === J.ui.cur ? ' cur' : '') + (g && g.v ? ' done' : '');
    th.querySelector('.sc').textContent = g && g.v ? g.v : '';
  }
  var cur = strip.children[J.ui.cur];
  if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: 'nearest', inline: 'center' });
};
