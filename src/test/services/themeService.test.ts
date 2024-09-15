import * as assert from 'assert';
import * as vscode from 'vscode';
import axios from 'axios';
import { getThemes, fetchThemeFile, fetchThemes } from '../../services/themeService';
import { Theme } from '../../types';
import { mockThemes } from '../constants';

suite('Theme Service Test Suite', () => {
  test('fetchThemes() fetches themes from API', async function () {
    const themes = await fetchThemes('mostinstalled');
    assert.strictEqual(themes[0].categories[0].includes('Themes'), true);
    assert.strictEqual(themes[0].theme_files.length > 0, true);
  });

  test('fetchThemeFile() fetches theme file from API', async function () {
    const themes = await fetchThemes('mostinstalled');
    const themeFileUrl = themes[0].theme_files[0].file;
    const themeFile = await fetchThemeFile(themeFileUrl);
    assert.strictEqual(Object.keys(themeFile.colors).length > 0, true);
  });

  test('getThemes() fetches themes from cache', async function () {
    const mockContext = {
      globalState: {
        get: async () => {
          return { themes: mockThemes, timestamp: Date.now() };
        },
      },
    };

    const themes = await getThemes(mockContext as unknown as vscode.ExtensionContext, 'mostinstalled');
    assert.strictEqual(themes[0].categories[0].includes('Themes'), true);
    assert.strictEqual(themes[0].theme_files.length > 0, true);
  });
});
