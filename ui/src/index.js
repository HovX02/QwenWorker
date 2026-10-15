function reply(data, status=200) { return Response.json(data, {status}); }
export default {
 async fetch(request, env) {
  const url = new URL(request.url);
  if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
  if (request.method === "OPTIONS") return new Response(null, {status:204, headers:{
   "Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type,X-App-Password"}});
  if (request.headers.get("Origin") && request.headers.get("Origin") !== url.origin) return reply({error:"Cross-origin blocked."},403);
  if (!env.APP_PASSWORD || request.headers.get("X-App-Password") !== env.APP_PASSWORD) return reply({error:"Incorrect app password."},401);
  if (!env.RUNPOD_API_KEY || !env.RUNPOD_ENDPOINT_ID) return reply({error:"RunPod secrets are not configured."},500);
  const base = `https://api.runpod.ai/v2/${env.RUNPOD_ENDPOINT_ID}`;
  const headers = {"Authorization":`Bearer ${env.RUNPOD_API_KEY}`,"Content-Type":"application/json"};
  try {
   if (request.method==="POST" && url.pathname==="/api/run") {
    const body = await request.text();
    if (body.length > 12_000_000) return reply({error:"Request too large; resize the image."},413);
    const r = await fetch(`${base}/run`, {method:"POST",headers,body});
    return new Response(await r.text(), {status:r.status,headers:{"Content-Type":"application/json"}});
   }
   const m=url.pathname.match(/^\/api\/status\/([A-Za-z0-9_-]+)$/);
   if (request.method==="GET" && m) {
    const r=await fetch(`${base}/status/${m[1]}`,{headers});
    return new Response(await r.text(),{status:r.status,headers:{"Content-Type":"application/json"}});
   }
   return reply({error:"Not found."},404);
  } catch(e) { return reply({error:"Proxy error: "+String(e.message||e)},502); }
 }
};
