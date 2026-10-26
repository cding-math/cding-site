'use strict';

const emailContainer = document.getElementById('email');
if (emailContainer) {
  const address = ['cding', 'math.ucla.edu'].join('@');
  const link = document.createElement('a');
  link.href = 'mailto:' + address;
  link.textContent = address;
  emailContainer.appendChild(link);
}

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
