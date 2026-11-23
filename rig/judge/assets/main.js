/* Start-up: load saved grades and resume at the first item not yet scored. */

(function () {
  J.load();
  var list = J.list();
  var start = Math.max(0, Math.min(J.state.cursor || 0, list.length - 1));
  if (J.graded(list[start].id)) {
    var next = J.nextUngraded(start);
    if (next >= 0) start = next;
  }
  J.ui.cur = start;

  document.addEventListener('keydown', J.onKeyDown);
  document.addEventListener('keyup', J.onKeyUp);
  window.addEventListener('blur', function () { J.flip('item'); });
  J.$('note').addEventListener('input', J.onNoteInput);
  J.$('btn-save').addEventListener('click', function () { J.saveGrades(); });
  J.$('btn-help').addEventListener('click', J.showHelp);
  J.$('btn-import').addEventListener('click', function () { J.$('file').click(); });
  J.$('file').addEventListener('change', function (e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      J.toast(J.importData(reader.result) ? 'Grades imported and merged.' : 'That file is not from this page.');
      J.render();
    };
    reader.readAsText(file);
  });
  J.$('overlay').addEventListener('click', function (e) { if (e.target.id === 'overlay') J.hideOverlay(); });

  J.render();
  if (!J.countGraded()) J.showHelp();
  if (J.restored) J.toast('Your grades were restored from the browser backup.');
})();
