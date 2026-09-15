import { expect, test } from '@playwright/test';
import axios from 'axios';
import { resolveApiBaseUrl } from '../../src/config/api';
import { OpenAPI } from '../../src/client/core/OpenAPI';
import { request } from '../../src/client/core/request';

const cases = [
    { name: 'unset', value: undefined, base: '' },
    { name: 'empty', value: '', base: '' },
    { name: 'whitespace', value: '   ', base: '' },
    { name: 'root', value: '/', base: '' },
    { name: 'absolute origin', value: 'http://localhost:5253', base: 'http://localhost:5253' },
    { name: 'trailing slash', value: ' https://valve-stems.local/ ', base: 'https://valve-stems.local' },
];

for (const { name, value, base } of cases) {
    test(`API URL: ${name}`, async () => {
        const resolved = resolveApiBaseUrl(value);
        expect(resolved).toBe(base);

        let capturedUrl: string | undefined;
        const client = axios.create({
            adapter: async (config) => {
                capturedUrl = config.url;
                return { data: [], status: 200, statusText: 'OK', headers: {}, config };
            },
        });
        await request({ ...OpenAPI, BASE: resolved }, {
            method: 'GET',
            url: '/api/v1/turbines/search',
        }, client);
        expect(capturedUrl).toBe(`${base}/api/v1/turbines/search`);
    });
}
