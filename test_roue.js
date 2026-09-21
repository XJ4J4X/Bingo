const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

const html = fs.readFileSync('public/roue.html', 'utf8');
const script = fs.readFileSync('public/roue.js', 'utf8');

const dom = new JSDOM(html, { 
  url: "http://localhost/", 
  runScripts: "outside-only" 
});

try {
    dom.window.eval(script);
    console.log("Script executed successfully.");
} catch (e) {
    console.error("FATAL ERROR ON LOAD:", e);
}
