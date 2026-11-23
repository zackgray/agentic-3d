/* Grades leave the page as a file: written beside the page when the local server serves it, downloaded otherwise. */

J.served = function () { return location.protocol === 'http:' || location.protocol === 'https:'; };

J.savedOk = function (msg) {
  J.state.exportedChanges = J.state.changes;
  J.save();
  J.render();
  J.toast(msg);
};

J.saveGrades = function () {
  var left = J.list().length - J.countGraded();
  var tail = left ? ' (' + left + ' still unscored)' : '';
  if (!J.served() || !window.fetch) { J.download(); J.savedOk('Grades file downloaded' + tail + '.'); return; }
  fetch('__grades__', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(J.exportData(), null, 1) })
    .then(function (r) { if (!r.ok) throw new Error('status ' + r.status); return r.json(); })
    .then(function (j) { J.savedOk('Grades file written beside the page: ' + j.saved + tail); })
    .catch(function () { J.download(); J.savedOk('The server could not save it, so the file was downloaded instead.'); });
};
