/**
 * Minimal Jest transform for single-file components, built on Vue's own
 * compiler. (vue-jest 5 alpha doesn't support Jest 29.) Styles are ignored;
 * the script and template are compiled together, then run through Babel
 * with the project config so imports become CommonJS.
 */
const crypto = require('crypto')
const { parse, compileScript, compileTemplate } = require('@vue/compiler-sfc')
const babel = require('@babel/core')

function compile(src, filename) {
  const { descriptor, errors } = parse(src, { filename })
  if (errors.length) throw errors[0]
  const id = crypto.createHash('md5').update(filename).digest('hex').slice(0, 8)

  if (descriptor.script || descriptor.scriptSetup) {
    return compileScript(descriptor, { id, inlineTemplate: true }).content
  }
  const tpl = compileTemplate({ source: descriptor.template.content, filename, id })
  return `${tpl.code.replace('export function render', 'function render')}\nexport default { render }`
}

module.exports = {
  process(src, filename) {
    const code = compile(src, filename)
    const out = babel.transformSync(code, { filename: `${filename}.js`, sourceMaps: 'inline' })
    return { code: out.code }
  },
  getCacheKey(src, filename) {
    return crypto.createHash('md5').update(src).update(filename).update('vueTransform-1').digest('hex')
  }
}
