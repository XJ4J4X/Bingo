const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const dom = new JSDOM(\`
<style>.hidden { display: none !important; }</style>
<div id="m" class="hidden" style="display: flex;"></div>
\`);
const el = dom.window.document.getElementById('m');
const computed = dom.window.getComputedStyle(el);
console.log('DISPLAY IS:', computed.display);
