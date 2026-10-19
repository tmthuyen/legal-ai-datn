import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // CI chạy `npm test -- --passWithNoTests` — project chưa có test,
    // bật sẵn option để không fail khi chưa có file test
    passWithNoTests: true,
    include: ['**/*.{test,spec}.?(c|m)[jt]s?(x)'],
    exclude: ['**/node_modules/**', '**/.next/**', '**/dist/**'],
  },
});
