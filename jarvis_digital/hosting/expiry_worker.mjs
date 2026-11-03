/** Original Pages runtime. Demo registry is compiled at deployment, never a public file. */
export function createFetch(registry, clock = Date.now) {
  const secure = (response) => {
    const headers = new Headers(response.headers);
    headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive');
    headers.set('Cache-Control', 'no-store');
    headers.set('X-Content-Type-Options', 'nosniff');
    headers.set('Referrer-Policy', 'no-referrer');
    return new Response(response.body, { status: response.status, headers });
  };
  const reply = (text, status) => secure(new Response(text, { status, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }));
  return async (request, env) => {
    if (!['GET', 'HEAD'].includes(request.method)) return reply('Method not allowed', 405);
    let path;
    try { path = decodeURIComponent(new URL(request.url).pathname); } catch { return reply('Not found', 404); }
    const parts = path.split('/').filter(Boolean);
    if (parts.some(part => part.startsWith('.') || part.includes('\\') || /^(?:_worker|package_meta|crm|credentials|secret)/i.test(part))) return reply('Not found', 404);
    if (!parts.length) return reply('Jarvis Digital — demonstrações conceituais não oficiais.', 200);
    if (path === '/robots.txt') return reply('User-agent: *\nDisallow: /\n', 200);
    const slug = parts[0];
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || !Object.hasOwn(registry, slug)) return reply('Not found', 404);
    const demo = registry[slug];
    const expires = Date.parse(demo.expires_at);
    if (demo.active !== true || !Number.isFinite(expires) || clock() >= expires) return reply('Demonstração indisponível ou expirada.', 410);
    const requested = parts.length === 1 ? 'index.html' : parts.slice(1).join('/');
    if (!Object.hasOwn(demo.files || {}, requested)) return reply('Not found', 404);
    const assetURL = new URL(request.url);
    assetURL.pathname = '/' + slug + '/' + requested;
    return secure(await env.ASSETS.fetch(new Request(assetURL, request)));
  };
}