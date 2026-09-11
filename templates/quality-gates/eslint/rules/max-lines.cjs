'use strict';

/**
 * Soft architectural pressure: max lines per file.
 * Severity is chosen by the host config (warn vs error).
 */
function createMaxLinesRule(defaultMax) {
  const maxDefault = typeof defaultMax === 'number' ? defaultMax : 350;

  return {
    meta: {
      type: 'suggestion',
      docs: {
        description: 'Limit physical lines per file (configurable via rule options or MAX_LINES).',
      },
      schema: [
        {
          type: 'object',
          properties: {
            max: { type: 'integer', minimum: 1 },
            skipBlankLines: { type: 'boolean' },
            skipComments: { type: 'boolean' },
          },
          additionalProperties: false,
        },
      ],
      messages: {
        tooLong: 'File has {{count}} lines (max {{max}}). Split by responsibility before raising the limit.',
      },
    },
    create(context) {
      const option = context.options[0] || {};
      const envMax = Number.parseInt(process.env.MAX_LINES || '', 10);
      const max = option.max || (Number.isFinite(envMax) ? envMax : maxDefault);
      const skipBlank = option.skipBlankLines !== false;
      const skipComments = option.skipComments === true;

      return {
        Program(node) {
          const source = context.sourceCode ?? context.getSourceCode();
          const lines = source.lines || source.getText().split(/\r?\n/);
          let count = 0;
          for (const line of lines) {
            const trimmed = line.trim();
            if (skipBlank && trimmed === '') continue;
            if (skipComments && (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*'))) {
              continue;
            }
            count += 1;
          }
          if (count > max) {
            context.report({
              node,
              messageId: 'tooLong',
              data: { count: String(count), max: String(max) },
            });
          }
        },
      };
    },
  };
}

module.exports = { createMaxLinesRule };
