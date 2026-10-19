import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tsLint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

const eslintConfig = defineConfig([
  // 1. Cấu hình các file bỏ qua (Global Ignores)
  globalIgnores(['.next/**', 'out/**', 'build/**', 'next-env.d.ts']),

  // 2. Kế thừa cấu hình từ Next.js
  ...nextVitals,
  ...nextTs,

  // 3. Cấu hình các quy tắc tùy chỉnh (Custom Rules)
  {
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      '@typescript-eslint': tsLint,
    },
    languageOptions: {
      parser: tsParser,
    },
    rules: {
      // Tích hợp các quy tắc chuẩn của React Hooks
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // 🛠️ CẤU HÌNH TAB / INDENT (2 Spaces)
      indent: ['error', 2, { SwitchCase: 1 }],

      // 🛠️ CẤU HÌNH DẤU NHÁY ĐƠN (Single Quotes)
      quotes: ['error', 'single', { avoidEscape: true, allowTemplateLiterals: true }],

      // 🛠️ CÁC CẤU HÌNH TỐT NHẤT CHO DỰ ÁN PRODUCTION
      semi: ['error', 'always'], // Bắt buộc có dấu chấm phẩy (;) cuối câu
      'no-trailing-spaces': 'error', // Không cho phép khoảng trắng thừa cuối dòng
      'comma-dangle': ['error', 'always-multiline'], // Bắt buộc dấu phẩy cuối cùng nếu xuống dòng
      'object-curly-spacing': ['error', 'always'], // Dấu cách đều trong ngoặc nhọn { abc }

      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          // Cảnh báo biến khai báo nhưng không dùng
          vars: 'all',
          args: 'after-used',
          ignoreRestSiblings: true,
        },
      ],
      '@typescript-eslint/no-explicit-any': 'off', // Tắt cảnh báo khi lạm dụng kiểu 'any'

      // Rule mới của eslint-plugin-react-hooks v7 (React Compiler-era).
      // Hạ xuống warning cho codebase hiện tại; có thể nâng lại sau khi refactor các effect.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
]);

export default eslintConfig;
