/* The scoring panel, the note line and the overlays. */

J.renderPanel = function () {
  var it = J.curItem(), g = it ? J.gradeOf(it.id) : null;
  J.$('product').textContent = it ? 'Product: ' + it.product : '';
  J.$('question').textContent = J.D.title;
  var scale = J.$('scale');
  scale.innerHTML = '';
  J.D.scores.forEach(function (s) {
    var row = document.createElement('div');
    row.className = 'lv' + (g && g.v === s.v ? ' on' : '');
    row.innerHTML = '<kbd></kbd><span></span>';
    row.firstChild.textContent = s.v;
    row.lastChild.textContent = s.label;
    row.addEventListener('click', function () { J.score(s.v); });
    scale.appendChild(row);
  });
  var box = J.$('note');
  if (document.activeElement !== box) box.value = g ? g.note || '' : '';
};

J.onNoteInput = function () {
  var it = J.curItem();
  if (it) J.setNote(it.id, J.$('note').value);
};

J.showOverlay = function (html) {
  var o = J.$('overlay');
  o.innerHTML = html;
  o.hidden = false;
};

J.hideOverlay = function () { J.$('overlay').hidden = true; };
J.overlayOpen = function () { return !J.$('overlay').hidden; };

J.showHelp = function () {
  var rows = [
    ['1 to 5', 'score the shape of this build'], ['Left / Right', 'previous / next item'],
    ['Enter', 'next item not yet scored'], ['Backspace', 'clear the score on this item'],
    ['hold R', 'flip to the reference model (same four views)'], ['hold P', 'flip to the product photo'],
    ['Z', 'fit the image to the window / show it at 100%'],
    ['N', 'type a note (Enter or Esc to finish)'], ['E', 'save your grades file'], ['?', 'this list'], ['Esc', 'close']];
  var scale = J.D.scores.map(function (s) { return '<tr><td><kbd>' + s.v + '</kbd></td><td>' + s.label + '</td></tr>'; });
  J.showOverlay('<h2>' + J.D.title + '</h2><table>' + scale.join('') + '</table><h2>Keys</h2><table>' +
    rows.map(function (r) { return '<tr><td><kbd>' + r[0] + '</kbd></td><td>' + r[1] + '</td></tr>'; }).join('') +
    '</table><p>Items are shuffled and carry no names beyond the product. Scores save in this browser as you go; ' +
    'save the grades file (E) when you finish: it is what the reveal reads. Served by the local server, the file is ' +
    'written beside this page; opened from disk, it downloads.</p><p><kbd>Enter</kbd> to start.</p>');
};
