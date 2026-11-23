/* Grades, sessions and browser storage. Nothing here knows which arm made which build. */
var J = { D: window.JUDGE, ui: { cur: 0, view: 'item', actual: false } };

J.KEY = 'agentic3d-judge::' + J.D.experiment + '::' + J.D.buildId;
J.FORMAT = J.D.format;
J.SCORES = J.D.scores.map(function (s) { return s.v; });
J.BACKUPS = 5;

J.fresh = function () {
  return { format: J.FORMAT, experiment: J.D.experiment, buildId: J.D.buildId, sessions: [], grades: {},
           cursor: 0, changes: 0, exportedChanges: 0 };
};

J.parse = function (text) {
  try {
    var s = JSON.parse(text);
    return s && s.format === J.FORMAT && s.buildId === J.D.buildId ? s : null;
  } catch (e) { return null; }
};

J.load = function () {
  var s = J.parse(localStorage.getItem(J.KEY));
  if (!s) {  // primary missing or damaged: fall back to the newest backup that parses
    var baks = [];
    try { baks = JSON.parse(localStorage.getItem(J.KEY + '::bak') || '[]'); } catch (e) { baks = []; }
    for (var i = baks.length - 1; i >= 0 && !s; i--) { s = J.parse(baks[i].json); if (s) J.restored = true; }
  }
  J.state = s || J.fresh();
  J.state.changes = J.state.changes || 0;
  J.state.exportedChanges = J.state.exportedChanges || 0;
  J.session = 's' + Date.now().toString(36);
  J.state.sessions = J.state.sessions || [];
  J.state.sessions.push({ id: J.session, started: new Date().toISOString() });
  J.save();
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist();
};

J.save = function () {
  var text = JSON.stringify(J.state);
  try {
    localStorage.setItem(J.KEY, text);
    if (J.state.changes % 10 === 0) {
      var baks = [];
      try { baks = JSON.parse(localStorage.getItem(J.KEY + '::bak') || '[]'); } catch (e) { baks = []; }
      baks.push({ t: Date.now(), json: text });
      localStorage.setItem(J.KEY + '::bak', JSON.stringify(baks.slice(-J.BACKUPS)));
    }
    J.saveFailed = false;
  } catch (e) { J.saveFailed = true; }
};

J.list = function () { return J.D.items; };
J.gradeOf = function (id) { return J.state.grades[id] || null; };
J.graded = function (id) { var g = J.gradeOf(id); return !!(g && g.v); };

J.touch = function () { J.state.changes += 1; J.save(); };

J.setScore = function (id, v) {
  var old = J.state.grades[id] || {};
  J.state.grades[id] = { v: v, note: old.note || '', s: J.session, t: Date.now() };
  J.touch();
};

J.setNote = function (id, text) {
  var g = J.state.grades[id] || (J.state.grades[id] = { v: null, note: '', s: J.session });
  g.note = text;
  g.t = Date.now();
  J.touch();
};

J.clearScore = function (id) {
  var g = J.state.grades[id];
  if (!g || !g.v) return;
  if (g.note) { g.v = null; g.t = Date.now(); } else delete J.state.grades[id];
  J.touch();
};

J.countGraded = function () {
  return J.list().filter(function (it) { return J.graded(it.id); }).length;
};

J.unexported = function () { return J.state.changes - J.state.exportedChanges; };

J.exportData = function () {
  var s = J.state;
  return { format: J.FORMAT, experiment: s.experiment, buildId: s.buildId, exportedAt: new Date().toISOString(),
           sessions: s.sessions, grades: s.grades };
};

J.download = function () {
  var text = JSON.stringify(J.exportData(), null, 1);
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
  a.download = 'grades-' + J.D.buildId + '-' + new Date().toISOString().replace(/[:.]/g, '-') + '.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

/* import keeps, per item, whichever grade was set last */
J.importData = function (text) {
  var d = J.parse(text);
  if (!d) return false;
  Object.keys(d.grades || {}).forEach(function (id) {
    var mine = J.state.grades[id], theirs = d.grades[id];
    if (!mine || (theirs.t || 0) > (mine.t || 0)) J.state.grades[id] = theirs;
  });
  J.touch();
  return true;
};
