import test from 'node:test';
import assert from 'node:assert/strict';
import { createFetch } from './expiry_worker.mjs';
const now = Date.parse('2026-11-03T12:00:00Z');
const registry = {
  active: {active:true,expires_at:'2026-11-04T12:00:00Z',files:{'index.html':'hash','assets/app.js':'hash'}},
  expired: {active:true,expires_at:'2026-11-02T12:00:00Z',files:{'index.html':'hash'}},
  disabled: {active:false,expires_at:'2026-11-04T12:00:00Z',files:{'index.html':'hash'}},
  invalid: {active:true,expires_at:'invalid',files:{'index.html':'hash'}}
};
const fetchDemo = createFetch(registry,()=>now);
const env = {ASSETS:{fetch:async(req)=>new Response(new URL(req.url).pathname,{status:200})}};
const call = (path,method='GET')=>fetchDemo(new Request('https://jarvis-digital.pages.dev'+path,{method}),env);
test('active demo resolves individual slug and noindex headers',async()=>{const r=await call('/active');assert.equal(r.status,200);assert.equal(await r.text(),'/active/index.html');assert.match(r.headers.get('X-Robots-Tag'),/noindex/);assert.equal(r.headers.get('Cache-Control'),'no-store');});
test('expired demo blocked server-side',async()=>assert.equal((await call('/expired')).status,410));
test('disabled demo blocked',async()=>assert.equal((await call('/disabled')).status,410));
test('invalid expiration fails closed',async()=>assert.equal((await call('/invalid')).status,410));
test('unknown slug blocked',async()=>assert.equal((await call('/unknown')).status,404));
test('private and unlisted files never reach assets',async()=>{for(const p of ['/active/.env','/active/PACKAGE_META.json','/active/crm.json','/active/hidden.html'])assert.equal((await call(p)).status,404,p);});
test('state-changing methods blocked',async()=>assert.equal((await call('/active','POST')).status,405));
test('only compiled allowlisted asset paths accepted',async()=>{const r=await call('/active/assets/app.js');assert.equal(r.status,200);assert.equal(await r.text(),'/active/assets/app.js');});
test('robots explicitly disallows indexing',async()=>{const r=await call('/robots.txt');assert.match(await r.text(),/Disallow: \//);});
test('expiration boundary is inclusive',async()=>{const f=createFetch(registry,()=>Date.parse(registry.active.expires_at));assert.equal((await f(new Request('https://jarvis-digital.pages.dev/active'),env)).status,410);});