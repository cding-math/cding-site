'use strict';

const emailContainer = document.getElementById('email');
if (emailContainer) {
  const address = ['cding', 'math.ucla.edu'].join('@');
  const link = document.createElement('a');
  link.href = 'mailto:' + address;
  link.textContent = address;
  emailContainer.appendChild(link);
}

// The mobile/touch heading is plain text. Only wide, fine-pointer layouts
// expose this native control; CSS also supports hover/focus without JavaScript.
(() => {
  const button = document.querySelector('.name-toggle');
  if (!button) return;
  const mode = window.matchMedia('(min-width: 800px) and (hover: hover) and (pointer: fine)');
  let hovering = button.matches(':hover');
  let keyboardFocused = button.matches(':focus-visible');
  let selected = false;
  let dismissed = false;

  function render() {
    button.setAttribute('aria-pressed', String(mode.matches &&
      (selected || ((hovering || keyboardFocused) && !dismissed))));
  }

  function dismiss() {
    selected = false;
    dismissed = true;
    render();
  }

  button.dataset.enhanced = '';
  render();
  button.addEventListener('pointerenter', event => {
    if (event.pointerType === 'touch') return;
    hovering = true;
    dismissed = false;
    render();
  });
  button.addEventListener('pointerleave', () => {
    hovering = false;
    if (!keyboardFocused) dismissed = false;
    render();
  });
  button.addEventListener('focus', () => {
    keyboardFocused = button.matches(':focus-visible');
    dismissed = false;
    render();
  });
  button.addEventListener('blur', () => {
    keyboardFocused = false;
    dismiss();
  });
  button.addEventListener('click', () => {
    selected = button.getAttribute('aria-pressed') !== 'true';
    dismissed = !selected;
    render();
  });
  button.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      event.preventDefault();
      dismiss();
    }
  });
  button.addEventListener('pointercancel', dismiss);
  document.addEventListener('pointerdown', event => {
    if (!button.contains(event.target)) dismiss();
  });
  mode.addEventListener('change', () => {
    hovering = false;
    keyboardFocused = false;
    dismiss();
  });
})();

if (typeof renderMathInElement === 'function') {
  renderMathInElement(document.body, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false},
    ],
    trust: false,
    maxExpand: 1000,
    maxSize: 20,
  });
}
