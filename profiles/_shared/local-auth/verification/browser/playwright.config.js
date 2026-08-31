import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'.',testMatch:'*.spec.js',workers:1,timeout:60000,use:{baseURL:'https://localhost:8443',ignoreHTTPSErrors:true,viewport:{width:1280,height:800},trace:'off',video:'off',screenshot:'off'},reporter:'line'});
