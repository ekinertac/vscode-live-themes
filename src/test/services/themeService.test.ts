// import * as assert from 'assert';
// import * as vscode from 'vscode';
// import * as sinon from 'sinon';
// import axios from 'axios';
// import { getThemes, fetchThemeFile } from '../../services/themeService';
// import { Theme } from '../../types';
// import { mockThemes } from '../constants';

// suite('Theme Service Test Suite', () => {
//   let mockContext: vscode.ExtensionContext;
//   let axiosStub: sinon.SinonStub;

//   setup(() => {
//     mockContext = {
//       globalState: {
//         get: sinon.stub(),
//         update: sinon.stub().resolves(),
//       },
//     } as unknown as vscode.ExtensionContext;

//     axiosStub = sinon.stub(axios, 'get');
//     process.env.VSCODE_DEBUG_MODE = 'false';
//   });

//   teardown(() => {
//     sinon.restore();
//   });

//   test('getThemes() fetches themes from API when cache is empty', async () => {
//     axiosStub.resolves({ data: mockThemes });
//     const result = await getThemes(mockContext, 'theme_list');

//     assert.deepStrictEqual(result, mockThemes);
//     assert.strictEqual(axiosStub.callCount, 1);
//   });

//   test('getThemes() returns cached themes if available and not expired', async () => {
//     const cachedThemes: Theme[] = mockThemes;
//     (mockContext.globalState.get as sinon.SinonStub).returns({
//       themes: cachedThemes,
//       timestamp: Date.now() - 23 * 60 * 60 * 1000, // 23 hours ago
//     });

//     const result = await getThemes(mockContext, 'theme_list');

//     assert.deepStrictEqual(result, cachedThemes);
//     assert.strictEqual(axiosStub.callCount, 0);
//   });

//   test('getThemes() fetches new themes if cache is expired', async () => {
//     const cachedThemes: Theme[] = mockThemes;
//     (mockContext.globalState.get as sinon.SinonStub).returns({
//       themes: cachedThemes,
//       timestamp: Date.now() - 25 * 60 * 60 * 1000, // 25 hours ago
//     });
//     axiosStub.resolves({ data: mockThemes });

//     const result = await getThemes(mockContext, 'theme_list');

//     assert.deepStrictEqual(result, mockThemes);
//     assert.strictEqual(axiosStub.callCount, 1);
//   });

//   test('getThemes() always fetches themes in development mode', async () => {
//     process.env.VSCODE_DEBUG_MODE = 'true';
//     axiosStub.resolves({ data: mockThemes });

//     const result = await getThemes(mockContext, 'theme_list');

//     assert.deepStrictEqual(result, mockThemes);
//     assert.strictEqual(axiosStub.callCount, 1);
//   });

//   test('fetchThemeFile() fetches and parses JSON theme file', async () => {
//     const mockThemeContent = '{ "name": "Test Theme", "colors": {} }';
//     axiosStub.resolves({ data: mockThemeContent });

//     const result = await fetchThemeFile('theme_url');

//     assert.deepStrictEqual(result, { name: 'Test Theme', colors: {} });
//   });

//   test('fetchThemeFile() handles non-string response data', async () => {
//     const mockThemeContent = { name: 'Test Theme', colors: {} };
//     axiosStub.resolves({ data: mockThemeContent });

//     const result = await fetchThemeFile('theme_url');

//     assert.deepStrictEqual(result, mockThemeContent);
//   });
// });
