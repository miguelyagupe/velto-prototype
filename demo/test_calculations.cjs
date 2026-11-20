// Execute the actual application's handlers with a minimal DOM adapter.
// This verifies computation, not browser layout or screen recording.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const make=()=>({value:'',textContent:'',className:'',style:{},children:[],append(...x){this.children.push(...x)},replaceChildren(){this.children=[]}});
const ids=Object.fromEntries(['csv','sort','minimum','total','mean','count','chart','rows','status','run','reset','filter'].map(x=>[x,make()]));
ids.csv.value=html.match(/<textarea[^>]*>([\s\S]*?)<\/textarea>/)[1];ids.sort.value='input';ids.minimum.value='0';
const context={document:{querySelector:s=>ids[s.slice(1)],getElementById:id=>ids[id],createElement:make},console};
vm.createContext(context);vm.runInContext(html.match(/<script>([\s\S]*)<\/script>/)[1],context);
ids.run.onclick();assert.equal(ids.total.textContent,'12,000');assert.equal(ids.mean.textContent,'2,000');
ids.csv.value=ids.csv.value.replace('Jun,3000','Jun,4500');ids.run.onclick();assert.equal(ids.total.textContent,'13,500');
ids.csv.value='month,sales\nJan,1200\nFeb,invalid';ids.run.onclick();assert.match(ids.status.textContent,/non-negative/);assert.equal(ids.total.textContent,'13,500');
ids.reset.onclick();assert.equal(ids.total.textContent,'12,000');ids.sort.value='desc';ids.sort.onchange();assert.equal(ids.chart.children[0].children[2].textContent,'Jun');
ids.minimum.value='2000';ids.filter.onclick();assert.equal(ids.total.textContent,'7,500');assert.equal(ids.count.textContent,3);
console.log('PASS: actual app calculations, update, invalid-input preservation, reset, descending order and filter. Browser capture remains a separate test.');
