'use strict';

const emailContainer = document.getElementById('email');
if (emailContainer) {
  const address = ['cding', 'math.ucla.edu'].join('@');
  const link = document.createElement('a');
  link.href = 'mailto:' + address;
  link.textContent = address;
  emailContainer.appendChild(link);
}

// One reveal control works with mouse, keyboard, and touch at every width.
// CSS alone chooses the annotation's position, including during a resize.
(() => {
  const button = document.querySelector('.name-toggle');
  if (!button) return;
  let hovering = button.matches(':hover');
  let keyboardFocused = button.matches(':focus-visible');
  let selected = false;
  let dismissed = false;

  function render() {
    button.setAttribute('aria-pressed', String(
      selected || ((hovering || keyboardFocused) && !dismissed)));
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
})();
