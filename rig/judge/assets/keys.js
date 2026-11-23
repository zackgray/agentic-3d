/* Keyboard first. Holding R or P flips the viewer in place; letting go returns to the build. */

J.FLIP_KEYS = { KeyR: 'ref', KeyP: 'photo' };
J.SCORE_KEYS = { Digit1: 1, Digit2: 2, Digit3: 3, Digit4: 4, Digit5: 5,
                 Numpad1: 1, Numpad2: 2, Numpad3: 3, Numpad4: 4, Numpad5: 5 };

J.onKeyDown = function (e) {
  if (document.activeElement && document.activeElement.id === 'note') {
    if (e.key === 'Enter' || e.key === 'Escape') { document.activeElement.blur(); e.preventDefault(); J.render(); }
    return;
  }
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (J.overlayOpen()) {
    if (e.key === 'Enter' || e.key === 'Escape') { J.hideOverlay(); e.preventDefault(); }
    return;
  }
  var code = e.code;
  if (J.SCORE_KEYS[code]) { J.score(J.SCORE_KEYS[code]); e.preventDefault(); }
  else if (J.FLIP_KEYS[code]) { if (!e.repeat) J.flip(J.FLIP_KEYS[code]); e.preventDefault(); }
  else if (code === 'ArrowLeft') { J.goto(J.ui.cur - 1); e.preventDefault(); }
  else if (code === 'ArrowRight') { J.goto(J.ui.cur + 1); e.preventDefault(); }
  else if (code === 'Enter') { J.enter(); e.preventDefault(); }
  else if (code === 'Backspace' || code === 'Delete') {
    var it = J.curItem();
    if (it) { J.clearScore(it.id); J.afterChange(); }
    e.preventDefault();
  }
  else if (code === 'KeyN') { J.$('note').focus(); e.preventDefault(); }
  else if (code === 'KeyE') { J.saveGrades(); e.preventDefault(); }
  else if (code === 'KeyZ') { J.ui.actual = !J.ui.actual; J.showView(); e.preventDefault(); }
  else if (e.key === '?' || code === 'KeyH') { J.showHelp(); e.preventDefault(); }
};

J.onKeyUp = function (e) {
  if (J.FLIP_KEYS[e.code]) J.flip('item');
};
