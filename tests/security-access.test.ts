import { randomUUID } from 'node:crypto';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createServer, type ServerResponse } from 'node:http';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';

let pool: typeof import('../lib/db').pool;
let auth: typeof import('../lib/auth').auth;
let server: typeof import('../lib/server');
const origin = process.env.BETTER_AUTH_URL || 'http://localhost:3000';
const password = 'Security-test-only-random-' + randomUUID();
const users: Record<string, { id: string; cookie: string; email: string }> = {};
const first = randomUUID();
const second = randomUUID();
const room = randomUUID();
const item = randomUUID();
const source = randomUUID();
const version = randomUUID();
const otherSource = randomUUID();
const otherVersion = randomUUID();
const chunk = randomUUID();
const task = randomUUID();
const privateText = 'PRIVATE-HOUSEHOLD-EVIDENCE-' + randomUUID();
let mailDirectory = '';
let atlas: typeof import('../app/api/atlas/route');
let originals: typeof import('../app/api/sources/[id]/route');
let citations: typeof import('../app/api/citations/[id]/route');
let uploads: typeof import('../app/api/sources/route');
let retries: typeof import('../app/api/sources/[id]/retry/route');
let ask: typeof import('../app/api/ask/route');
let exportsRoute: typeof import('../app/api/export/route');
let creditExport: typeof import('../app/api/credits/export/route');
let workerMode = 'valid';
let workerCalls = 0;
let lastWorkerRequest: Record<string, unknown> = {};
let releaseWorker: (() => void) | undefined;
const pendingResponses = new Set<ServerResponse>();
const adversarialWorker = createServer(async (req, res) => {
  pendingResponses.add(res);
  res.on('close', () => pendingResponses.delete(res));
  const parts: Buffer[] = [];
  for await (const part of req) parts.push(Buffer.from(part));
  lastWorkerRequest = JSON.parse(Buffer.concat(parts).toString());
  if(req.url?.startsWith('/cache/')){res.setHeader('content-type','application/json');res.end(JSON.stringify({hit:false}));return;}
  workerCalls++;
  if (req.headers['x-worker-key'] !== process.env.WORKER_KEY) { res.writeHead(403); res.end(); return; }
  if (workerMode === 'failure') { res.writeHead(500); res.end(); return; }
  if (workerMode === 'delayed') await new Promise<void>(resolve => { releaseWorker = resolve; });
  res.setHeader('content-type', 'application/json');
  res.end(JSON.stringify({ answer: `Evidence: ${privateText}`, confidence: 'supported', mode: 'adversarial-test-worker',
    citations: [{ id: chunk, sourceId: source, versionId: version, text: workerMode === 'fabricated' ? 'Fabricated unsupported quote' : workerMode === 'empty' ? '' : privateText }],
    diagnostics: { privateWorkerInformation: 'owner only' },
  }));
});

function request(method = 'GET', role = 'owner', householdId = first, headers: Record<string, string> = {}) {
  return new Request(`${origin}/api/atlas?householdId=${householdId}`, {
    method, headers: { origin, cookie: users[role]?.cookie || '', ...headers },
  });
}
function action(body: Record<string, unknown>, role = 'owner', householdId = first) {
  return new Request(`${origin}/api/atlas?householdId=${householdId}`, {
    method: 'POST', headers: { origin, cookie: users[role].cookie, 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
}
function objectRequest(id: string, role = 'owner', householdId = first, suffix = '') {
  return new Request(`${origin}/api/sources/${id}?householdId=${householdId}${suffix}`, {
    headers: { cookie: users[role].cookie },
  });
}
function params(id: string) { return { params: Promise.resolve({ id }) }; }
function question(operationId: string, role = 'owner', householdId = first, extra: Record<string, unknown> = {}, signal?: AbortSignal) {
  return new Request(`${origin}/api/ask?householdId=${householdId}`, {
    method: 'POST', signal, headers: { origin, cookie: users[role].cookie, 'content-type': 'application/json' },
    body: JSON.stringify({ question: 'Which purifier filter?', operationId, ...extra }),
  });
}
async function waitForWorker() {
  for (let i = 0; i < 100 && !releaseWorker; i++) await new Promise(resolve => setTimeout(resolve, 10));
  expect(releaseWorker).toBeTypeOf('function');
}
function releaseWorkerResponse() { releaseWorker?.(); }
async function reservation(operationId: string) {
  return (await pool.query('SELECT * FROM credit_reservations WHERE operation_id=$1', [operationId])).rows[0];
}

beforeAll(async () => {
  process.env.BETTER_AUTH_SECRET ||= 'security-test-only-secret-36-characters';
  process.env.BETTER_AUTH_URL ||= origin;
  mailDirectory = await mkdtemp(path.join(tmpdir(), 'homeatlas-security-'));
  process.env.DATA_DIR = mailDirectory;
  process.env.STORAGE_ROOT = path.join(mailDirectory, 'storage');
  process.env.WORKER_KEY = 'security-adversarial-worker-' + randomUUID();
  await new Promise<void>(resolve => adversarialWorker.listen(0, '127.0.0.1', resolve));
  const address = adversarialWorker.address();
  if (!address || typeof address === 'string') throw new Error('Test worker did not start');
  process.env.WORKER_URL = `http://127.0.0.1:${address.port}`;
  ({ pool } = await import('../lib/db'));
  ({ auth } = await import('../lib/auth'));
  server = await import('../lib/server');
  for (const name of ['owner', 'editor', 'viewer', 'outsider']) {
    const email = `security-${name}-${randomUUID()}@example.invalid`;
    const created = await auth.api.signUpEmail({ body: { name, email, password }, headers: new Headers({ origin }) });
    users[name] = { id: created.user.id, cookie: '', email };
    // These are fixture accounts. User-facing email verification is tested separately.
    await pool.query('UPDATE "user" SET "emailVerified"=true WHERE id=$1', [created.user.id]);
    const signed = await auth.api.signInEmail({ body: { email, password }, headers: new Headers({ origin }), asResponse: true });
    expect(signed.status).toBe(200);
    users[name].cookie = signed.headers.getSetCookie().map(value => value.split(';')[0]).join('; ');
  }
  await pool.query('INSERT INTO households(id,name,created_by) VALUES($1,$2,$3),($4,$5,$6)', [first, 'Private household', users.owner.id, second, 'Other household', users.outsider.id]);
  await pool.query(`INSERT INTO memberships(household_id,user_id,role) VALUES
    ($1,$2,'owner'),($1,$3,'editor'),($1,$4,'viewer'),($5,$6,'owner')`, [first, users.owner.id, users.editor.id, users.viewer.id, second, users.outsider.id]);
  await pool.query('INSERT INTO rooms(id,household_id,name) VALUES($1,$2,$3)', [room, first, 'Private bedroom']);
  await pool.query('INSERT INTO items(id,household_id,room_id,name) VALUES($1,$2,$3,$4)', [item, first, room, 'Private purifier']);
  await mkdir(process.env.STORAGE_ROOT, { recursive: true });
  const sourcePath = path.join(process.env.STORAGE_ROOT, 'private.pdf');
  await writeFile(sourcePath, privateText, { mode: 0o600 });
  for (const [hid, sid, vid, actor] of [[first, source, version, users.owner.id], [second, otherSource, otherVersion, users.outsider.id]]) {
    const filePath = hid === first ? sourcePath : path.join(process.env.STORAGE_ROOT, 'other.pdf');
    const content = hid === first ? privateText : 'Other household document';
    if (hid !== first) await writeFile(filePath, content, { mode: 0o600 });
    await pool.query("INSERT INTO sources(id,household_id,title,mime_type,created_by,status) VALUES($1,$2,$3,'application/pdf',$4,'ready')", [sid, hid, 'Security fixture source', actor]);
    await pool.query("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES($1,$2,$3,1,$4,$5,$6,'application/pdf')", [vid, hid, sid, filePath, 'fixture-sha', Buffer.byteLength(content)]);
    await pool.query('UPDATE sources SET current_version_id=$1 WHERE id=$2', [vid, sid]);
  }
  await pool.query('INSERT INTO chunks(id,household_id,source_id,version_id,item_id,room_id,text,page,bbox) VALUES($1,$2,$3,$4,$5,$6,$7,1,$8)', [chunk, first, source, version, item, room, privateText, '[1,2,30,40]']);
  await pool.query("INSERT INTO tasks(id,household_id,item_id,title,due_date,created_by) VALUES($1,$2,$3,'Private task','2026-10-15',$4)", [task, first, item, users.owner.id]);
  atlas = await import('../app/api/atlas/route');
  originals = await import('../app/api/sources/[id]/route');
  citations = await import('../app/api/citations/[id]/route');
  uploads = await import('../app/api/sources/route');
  retries = await import('../app/api/sources/[id]/retry/route');
  ask = await import('../app/api/ask/route');
  exportsRoute = await import('../app/api/export/route');
  creditExport = await import('../app/api/credits/export/route');
}, 30000);

afterAll(async () => {
  releaseWorkerResponse();
  for (const response of pendingResponses) response.destroy();
  await new Promise<void>(resolve => adversarialWorker.close(() => resolve()));
  if (pool) {
    await pool.query('DELETE FROM households WHERE id=ANY($1::uuid[])', [[first, second]]);
    const ids = Object.values(users).map(user => user.id);
    if (ids.length) {
      await pool.query('DELETE FROM rate_limits WHERE key=ANY($1::text[])', [ids.flatMap(id => ['atlas:', 'ask:', 'upload:'].map(prefix => prefix + id))]);
      await pool.query('DELETE FROM audit_events WHERE actor_id=ANY($1::text[])', [ids]);
      await pool.query('DELETE FROM "user" WHERE id=ANY($1::text[])', [ids]);
    }
    await pool.end();
  }
  if (mailDirectory) await rm(mailDirectory, { recursive: true, force: true });
});

describe('independent real-handler tenant ID attacks', () => {
  it('scopes dashboard data and refuses an explicitly foreign household', async () => {
    const own = await atlas.GET(request());
    expect(own.status).toBe(200);
    expect((await own.json()).items.map((value: { id: string }) => value.id)).toContain(item);
    const other = await atlas.GET(request('GET', 'outsider', second));
    expect(other.status).toBe(200);
    const body = await other.text();
    expect(body).not.toContain(item);
    expect(body).not.toContain(room);
    expect(body).not.toContain(privateText);
    expect((await atlas.GET(request('GET', 'outsider', first))).status).toBe(404);
  });

  it('rejects foreign record updates, parent IDs, tasks, and body household IDs', async () => {
    for (const body of [
      { action: 'updateItem', id: item, name: 'Stolen item' },
      { action: 'addItem', roomId: room, name: 'Foreign parent' },
      { action: 'completeTask', id: task },
      { action: 'addTask', itemId: item, title: 'Foreign item task', dueDate: '2026-10-15' },
    ]) expect((await atlas.POST(action(body, 'outsider', second))).status).toBe(404);
    expect((await atlas.POST(action({ action: 'addRoom', name: 'Forged home', householdId: second }))).status).toBe(404);
    const record = await pool.query('SELECT name FROM items WHERE id=$1', [item]);
    expect(record.rows[0].name).toBe('Private purifier');
  });

  it('enforces viewer and editor roles inside real mutation handlers', async () => {
    expect((await atlas.POST(action({ action: 'addRoom', name: 'Forbidden room' }, 'viewer'))).status).toBe(403);
    for (const role of ['viewer', 'editor']) {
      expect((await atlas.POST(action({ action: 'invite', email: 'new@example.invalid', role: 'owner' }, role))).status).toBe(400);
      expect((await atlas.POST(action({ action: 'invite', email: 'new@example.invalid', role: 'viewer' }, role))).status).toBe(403);
      expect((await atlas.POST(action({ action: 'removeMember', userId: users.owner.id }, role))).status).toBe(403);
    }
    expect((await uploads.POST(request('POST', 'viewer'))).status).toBe(403);
    expect((await retries.POST(action({ operationId: randomUUID() }, 'viewer'), params(source))).status).toBe(403);
  });

  it('prevents demotion or removal of the last household owner', async () => {
    expect((await atlas.POST(action({ action: 'updateMember', userId: users.owner.id, role: 'viewer' }))).status).toBe(409);
    expect((await atlas.POST(action({ action: 'removeMember', userId: users.owner.id }))).status).toBe(409);
    const owners = await pool.query("SELECT user_id FROM memberships WHERE household_id=$1 AND role='owner'", [first]);
    expect(owners.rows).toHaveLength(1);
  });

  it('blocks viewer writes to shared item history through the bookmark action', async () => {
    const result = await atlas.POST(action({ action: 'bookmark', title: 'Viewer history injection', answer: 'Untrusted shared history', itemId: item }, 'viewer'));
    expect(result.status).toBe(403);
    const history = await pool.query('SELECT * FROM maintenance_events WHERE household_id=$1', [first]);
    expect(history.rows).toHaveLength(0);
  });

  it('stores only authorized canonical citations in a private viewer bookmark', async () => {
    const result = await atlas.POST(action({ action: 'bookmark', title: 'My source', citations: [{ id: chunk, sourceId: source, versionId: version, text: 'forged', storagePath: '/etc/passwd' }] }, 'viewer'));
    expect(result.status).toBe(200);
    const body = await result.json();
    expect(body.bookmark.citations[0].text).toBe(privateText);
    expect(body.bookmark.citations[0].storagePath).toBeUndefined();
    expect((await atlas.POST(action({ action: 'bookmark', title: 'Steal source', citations: [{ id: chunk, sourceId: source, versionId: version }] }, 'outsider', second))).status).toBe(404);
  });

  it('reauthorizes source files, metadata, versions, citations, and previews', async () => {
    for (const suffix of ['', '&metadata=true', `&version=${version}`]) {
      const denied = await originals.GET(objectRequest(source, 'outsider', second, suffix), params(source));
      expect(denied.status).toBe(404);
      expect(await denied.text()).not.toContain(privateText);
    }
    expect((await originals.GET(objectRequest(source, 'owner', first, `&version=${otherVersion}`), params(source))).status).toBe(404);
    for (const suffix of ['', '&preview=true']) expect((await citations.GET(objectRequest(chunk, 'outsider', second, suffix), params(chunk))).status).toBe(404);
    const allowed = await originals.GET(objectRequest(source, 'viewer'), params(source));
    expect(allowed.status).toBe(200);
    expect(await allowed.text()).toBe(privateText);
    expect(allowed.headers.get('cache-control')).toBe('private, no-store');
    const citation = await citations.GET(objectRequest(chunk, 'viewer'), params(chunk));
    expect(citation.status).toBe(200);
    const detail = await citation.json();
    expect(detail.text).toBe(privateText);
    expect(detail.imagePath).toBeUndefined();
  });

  it('rejects foreign source reprocessing before any credit reservation', async () => {
    const operationId = randomUUID();
    const denied = await retries.POST(action({ operationId }, 'outsider', second), params(source));
    expect(denied.status).toBe(404);
    const reservations = await pool.query('SELECT id FROM credit_reservations WHERE operation_id=$1', [operationId]);
    expect(reservations.rows).toHaveLength(0);
  });

  it('scopes exports, hides storage paths, and enforces owner-only household export', async () => {
    expect((await exportsRoute.GET(request('GET', 'viewer'))).status).toBe(403);
    expect((await exportsRoute.GET(request('GET', 'editor'))).status).toBe(403);
    expect((await exportsRoute.GET(request('GET', 'outsider', first))).status).toBe(404);
    const exported = await exportsRoute.GET(request());
    expect(exported.status).toBe(200);
    const body = await exported.text();
    expect(body).toContain(privateText);
    expect(body).not.toContain(mailDirectory);
    expect(body).not.toContain(otherVersion);
    const other = await exportsRoute.GET(request('GET', 'outsider', second));
    expect(other.status).toBe(200);
    expect(await other.text()).not.toContain(privateText);
    expect((await creditExport.GET(request('GET', 'outsider', first))).status).toBe(404);
    const ledger = await creditExport.GET(request('GET', 'outsider', second));
    expect(ledger.status).toBe(200);
    expect(await ledger.text()).not.toContain(users.owner.id);
  });
});

describe('adversarial worker transport with real question handlers and credit transactions', () => {
  it('rejects forged question scope before calling worker or reserving credits', async () => {
    const operationId = randomUUID();
    const calls = workerCalls;
    const response = await ask.POST(question(operationId, 'outsider', second, { itemId: item }));
    expect(response.status).toBe(404);
    expect(workerCalls).toBe(calls);
    expect(await reservation(operationId)).toBeUndefined();
  });

  it('charges one successful answer, replays idempotently, and binds operation to actor and input', async () => {
    workerMode = 'valid';
    const operationId = randomUUID();
    const calls = workerCalls;
    const response = await ask.POST(question(operationId));
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.citations[0].text).toBe(privateText);
    expect(lastWorkerRequest.actorId).toBe(users.owner.id);
    expect(lastWorkerRequest.householdId).toBe(first);
    expect((await reservation(operationId)).status).toBe('charged');
    const replay = await ask.POST(question(operationId));
    expect(replay.status).toBe(200);
    expect((await replay.json()).replayed).toBe(true);
    expect(workerCalls - calls).toBe(1);
    expect((await ask.POST(question(operationId, 'owner', first, { question: 'Changed question' }))).status).toBe(409);
    expect((await ask.POST(question(operationId, 'viewer'))).status).toBe(409);
    const charges = await pool.query("SELECT id FROM credit_ledger WHERE household_id=$1 AND operation_id=$2 AND kind='charge'", [first, operationId]);
    expect(charges.rows).toHaveLength(1);
  });

  it('rejects concurrent question replay while the first request is in flight', async () => {
    workerMode = 'delayed'; releaseWorker = undefined;
    const operationId = randomUUID();
    const pending = ask.POST(question(operationId));
    await waitForWorker();
    expect((await ask.POST(question(operationId))).status).toBe(409);
    releaseWorkerResponse();
    expect((await pending).status).toBe(200);
    workerMode = 'valid'; releaseWorker = undefined;
    expect((await reservation(operationId)).status).toBe('charged');
  });

  it('rejects cross-household evidence returned by a malicious worker and refunds it', async () => {
    workerMode = 'valid';
    const operationId = randomUUID();
    const response = await ask.POST(question(operationId, 'outsider', second));
    expect(response.status).toBe(502);
    expect(await response.text()).not.toContain(privateText);
    expect((await reservation(operationId)).status).toBe('refunded');
    const messages = await pool.query('SELECT id FROM messages WHERE household_id=$1 AND content LIKE $2', [second, `%${privateText}%`]);
    expect(messages.rows).toHaveLength(0);
  });

  it('rejects fabricated citation quotes and releases their reservation', async () => {
    workerMode = 'fabricated';
    const operationId = randomUUID();
    const logger = vi.spyOn(console, 'error').mockImplementation(() => {});
    try {
      const response = await ask.POST(question(operationId));
      expect(response.status).toBe(502);
      expect((await reservation(operationId)).status).toBe('refunded');
      const logs = JSON.stringify(logger.mock.calls);
      expect(logs).not.toContain(privateText);
      expect(logs).not.toContain('Fabricated unsupported quote');
      expect(logs).not.toContain(users.owner.cookie);
      expect(logs).not.toContain(process.env.WORKER_KEY);
    } finally { logger.mockRestore(); workerMode = 'valid'; }
  });

  it('rejects empty evidence quotes rather than accepting the substring match', async () => {
    workerMode = 'empty';
    const operationId = randomUUID();
    const response = await ask.POST(question(operationId));
    expect(response.status).toBeGreaterThanOrEqual(400);
    expect((await reservation(operationId)).status).toBe('refunded');
    workerMode = 'valid';
  });

  it('does not publish a late answer after stale reservation recovery refunded it', async () => {
    workerMode = 'delayed'; releaseWorker = undefined;
    const operationId = randomUUID();
    const before = await pool.query('SELECT count(*)::int AS count FROM conversations WHERE household_id=$1 AND user_id=$2', [first, users.editor.id]);
    const pending = ask.POST(question(operationId, 'editor'));
    await waitForWorker();
    await pool.query("UPDATE credit_reservations SET created_at=now()-interval '11 minutes' WHERE operation_id=$1", [operationId]);
    const { ensureMonthlyGrant } = await import('../lib/credits');
    await ensureMonthlyGrant(pool, first, users.owner.id);
    expect((await reservation(operationId)).status).toBe('refunded');
    releaseWorkerResponse();
    const response = await pending;
    expect(response.status).toBe(409);
    expect((await reservation(operationId)).result).toBeNull();
    const after = await pool.query('SELECT count(*)::int AS count FROM conversations WHERE household_id=$1 AND user_id=$2', [first, users.editor.id]);
    expect(after.rows[0].count).toBe(before.rows[0].count);
    workerMode = 'valid'; releaseWorker = undefined;
  });

  it('refunds failed and cancelled requests without persisting an answer', async () => {
    workerMode = 'failure';
    const failedId = randomUUID();
    expect((await ask.POST(question(failedId))).status).toBe(503);
    expect((await reservation(failedId)).status).toBe('refunded');
    workerMode = 'valid';
    const cancelledId = randomUUID();
    const controller = new AbortController(); controller.abort();
    expect((await ask.POST(question(cancelledId, 'editor', first, {}, controller.signal))).status).toBe(503);
    expect((await reservation(cancelledId)).status).toBe('refunded');
  });

  it('reauthorizes after inference and refunds a removed member without returning source text', async () => {
    workerMode = 'delayed'; releaseWorker = undefined;
    const operationId = randomUUID();
    const pending = ask.POST(question(operationId, 'viewer'));
    await waitForWorker();
    await pool.query('DELETE FROM memberships WHERE household_id=$1 AND user_id=$2', [first, users.viewer.id]);
    releaseWorkerResponse();
    const response = await pending;
    expect(response.status).toBe(403);
    expect(await response.text()).not.toContain(privateText);
    expect((await reservation(operationId)).status).toBe('refunded');
    await pool.query("INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,'viewer')", [first, users.viewer.id]);
    workerMode = 'valid'; releaseWorker = undefined;
  });

  it('omits administrator diagnostics from viewer question responses', async () => {
    workerMode = 'valid';
    const response = await ask.POST(question(randomUUID(), 'viewer'));
    expect(response.status).toBe(200);
    expect((await response.json()).diagnostics).toBeUndefined();
  });
});

describe('independent session and household authorization', () => {
  it('authenticates real signed cookies and resolves membership from PostgreSQL', async () => {
    const scope = await server.scope(request());
    expect(scope.user.id).toBe(users.owner.id);
    expect(scope.householdId).toBe(first);
    expect(scope.role).toBe('owner');
    expect(users.owner.cookie).toContain('session_token=');
  });

  it('rejects unauthenticated and tampered sessions', async () => {
    await expect(server.session(request('GET', 'missing'))).rejects.toMatchObject({ status: 401 });
    await expect(server.session(request('GET', 'owner', first, { cookie: users.owner.cookie + 'tampered' }))).rejects.toMatchObject({ status: 401 });
  });

  it('rejects a foreign household selected by query, parameter, or header', async () => {
    await expect(server.scope(request('GET', 'outsider', first))).rejects.toMatchObject({ status: 404 });
    await expect(server.scope(request('GET', 'outsider', second), first)).rejects.toMatchObject({ status: 404 });
    const header = new Request(`${origin}/api/atlas`, { headers: { cookie: users.outsider.cookie, 'x-household-id': first } });
    await expect(server.scope(header)).rejects.toMatchObject({ status: 404 });
  });

  it('denies forged cross-household room and item relationships', async () => {
    await expect(server.linkedIds(pool, second, item)).rejects.toMatchObject({ status: 404 });
    await expect(server.linkedIds(pool, second, null, room)).rejects.toMatchObject({ status: 404 });
    await expect(server.linkedIds(pool, first, item, randomUUID())).rejects.toMatchObject({ status: 400 });
    await expect(server.linkedIds(pool, first, item, room)).resolves.toBeUndefined();
  });

  it('enforces owner, editor, and viewer roles with database-derived membership', async () => {
    const viewer = await server.scope(request('GET', 'viewer'));
    const editor = await server.scope(request('GET', 'editor'));
    expect(() => server.requireRole(viewer, ['owner', 'editor'])).toThrow(/role/);
    expect(() => server.requireRole(editor, ['owner'])).toThrow(/role/);
    expect(() => server.requireRole(editor, ['owner', 'editor'])).not.toThrow();
  });

  it('rejects cross-origin, originless, and explicitly cross-site writes', () => {
    expect(() => server.sameOrigin(request('POST', 'owner', first, { origin: 'https://attacker.invalid' }))).toThrow(/HomeAtlas/);
    const missing = new Request(`${origin}/api/atlas`, { method: 'POST', headers: { cookie: users.owner.cookie } });
    expect(() => server.sameOrigin(missing)).toThrow(/HomeAtlas/);
    expect(() => server.sameOrigin(request('POST', 'owner', first, { 'sec-fetch-site': 'cross-site' }))).toThrow(/Cross-site/);
    expect(() => server.sameOrigin(request('POST'))).not.toThrow();
  });

  it('requires fresh authentication for an old session and validates reauthentication password', async () => {
    const req = request();
    await pool.query('UPDATE "session" SET "createdAt"=now()-interval \'16 minutes\' WHERE "userId"=$1', [users.owner.id]);
    try {
      const oldScope = await server.scope(req);
      await expect(server.freshAuthentication(req, oldScope)).rejects.toMatchObject({ status: 403 });
      await expect(server.freshAuthentication(req, oldScope, 'wrong-password')).rejects.toMatchObject({ status: 403 });
      await expect(server.freshAuthentication(req, oldScope, password)).resolves.toBeUndefined();
    } finally { await pool.query('UPDATE "session" SET "createdAt"=now() WHERE "userId"=$1', [users.owner.id]); }
  });

  it('observes role changes and removed membership on the next request', async () => {
    await pool.query("UPDATE memberships SET role='viewer' WHERE household_id=$1 AND user_id=$2", [first, users.editor.id]);
    const changed = await server.scope(request('GET', 'editor'));
    expect(changed.role).toBe('viewer');
    expect(() => server.requireRole(changed, ['owner', 'editor'])).toThrow(/role/);
    await pool.query('DELETE FROM memberships WHERE household_id=$1 AND user_id=$2', [first, users.editor.id]);
    await expect(server.scope(request('GET', 'editor'))).rejects.toMatchObject({ status: 404 });
    await pool.query("INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,'editor')", [first, users.editor.id]);
  });
});
