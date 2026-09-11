'use strict';

const { createMaxLinesRule } = require('./max-lines.cjs');

module.exports = {
  rules: {
    'max-file-lines': createMaxLinesRule(350),
  },
};
