import globals from "globals";
import tseslint from "typescript-eslint";
export default tseslint.config({ignores: ["dist/**", "coverage/**", "verification/**"]}, ...tseslint.configs.recommended, {files: ["**/*.{ts,tsx}"], languageOptions: {globals: {...globals.browser, ...globals.node}}});
