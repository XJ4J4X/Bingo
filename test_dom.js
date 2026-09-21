const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

const html = fs.readFileSync('public/index.html', 'utf8');
const script = fs.readFileSync('public/app.js', 'utf8');

const dom = new JSDOM(html, { 
  url: "http://localhost/", 
  runScripts: "outside-only" 
});

dom.window.localStorage.setItem('userPseudo', 'Aminat0_');
dom.window.localStorage.setItem('userPassword', 'secret');

try {
    dom.window.eval(script);
    console.log("Script executed successfully without fatal errors.");
} catch (e) {
    console.error("FATAL ERROR ON LOAD:", e);
}
