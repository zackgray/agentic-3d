/* Navigation and what the keys do. Rendering lives in view.js and panel.js. */

J.curItem = function () { return J.list()[J.ui.cur] || null; };

J.goto = function (i) {
  var n = J.list().length;
  if (!n) return;
  J.ui.cur = Math.max(0, Math.min(n - 1, i));
  J.state.cursor = J.ui.cur;
  J.save();
  J.render();
};

J.nextUngraded = function (from) {
  var list = J.list(), n = list.length;
  for (var k = 1; k <= n; k++) {
    var i = (from + k) % n;
    if (!J.graded(list[i].id)) return i;
  }
  return -1;
};

J.score = function (v) {
  var it = J.curItem();
  if (!it) return;
  J.setScore(it.id, v);
  J.afterChange();
  if (J.countGraded() === J.list().length) J.toast('Every item is scored. Press E to save the grades file.');
  else J.toast('Scored ' + v + '. Enter for the next unscored item.');
};

J.afterChange = function () {
  var pending = J.unexported();
  if (pending > 0 && pending % 25 === 0) J.toast(pending + ' changes since the last save. Press E to save a file.');
  J.render();
};

J.enter = function () {
  var it = J.curItem();
  if (!it) return;
  var next = J.nextUngraded(J.ui.cur);
  if (next < 0) { J.toast('Every item is scored. Saving your grades file.'); J.saveGrades(); }
  else if (next === J.ui.cur) J.toast('This is the last item not yet scored.');
  else J.goto(next);
};

J.flip = function (view) {
  J.ui.view = view;
  J.showView();
};
