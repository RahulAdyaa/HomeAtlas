import {defineConfig} from 'vitest/config';
import {fileURLToPath} from 'node:url';
export default defineConfig({
 resolve:{alias:{'@':fileURLToPath(new URL('.',import.meta.url))}},
 // Migration replay performs DDL on the shared schema; don't race it with fixture writes.
 // Promise.all race checks inside each test still run concurrently.
 test:{fileParallelism:false,include:['tests/**/*.test.ts'],testTimeout:30000},
});
