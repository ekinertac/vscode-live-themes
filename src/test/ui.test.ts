import * as assert from 'assert';
import * as vscode from 'vscode';
import {
  createCategoryQuickPick,
  createThemeQuickPick,
  createFileQuickPick,
  createSearchQuickPick,
} from '../ui/quickPicks';
import { mockThemes } from './constants';

suite('UI Test Suite', () => {
  suiteTeardown(() => {
    vscode.window.showInformationMessage('All tests done!');
  });

  test('createCategoryQuickPick()', () => {
    const quickPick = createCategoryQuickPick();
    assert.strictEqual(quickPick.items.length, 8);
    assert.strictEqual(quickPick.totalSteps, 3);
  });

  test('createThemeQuickPick()', () => {
    const quickPick = createThemeQuickPick(mockThemes);
    assert.strictEqual(quickPick.items.length, 3);
    assert.strictEqual(quickPick.totalSteps, 3);
    assert.strictEqual(quickPick.items[1].description, '2 Themes');
    assert.strictEqual(quickPick.title, 'Step 2/2: Select a theme');
  });

  test('createThemeQuickPick() with single theme', () => {
    const quickPick = createThemeQuickPick([mockThemes[1]]);
    assert.strictEqual(quickPick.items.length, 2);
    assert.strictEqual(quickPick.totalSteps, 3);
    assert.strictEqual(quickPick.items[1].description, '1 Theme');
    assert.strictEqual(quickPick.title, 'Step 2/2: Select a theme');
  });

  test('createFileQuickPick()', () => {
    const quickPick = createFileQuickPick(mockThemes[0]);
    assert.strictEqual(quickPick.items.length, 3);
    assert.strictEqual(quickPick.totalSteps, 3);
    assert.strictEqual(quickPick.title, 'Step 3/3: Select a theme file');
  });

  test('createFileQuickPick() empty theme_files', () => {
    const quickPick = createFileQuickPick({ ...mockThemes[1], theme_files: [] });
    assert.strictEqual(quickPick.items.length, 1);
    assert.strictEqual(quickPick.totalSteps, 3);
    assert.strictEqual(quickPick.title, 'Step 3/3: Select a theme file');
  });

  test('createSearchQuickPick()', () => {
    const quickPick = createSearchQuickPick();
    assert.strictEqual(quickPick.items.length, 2);
    assert.strictEqual(quickPick.totalSteps, 1);
    assert.strictEqual(quickPick.title, 'Search themes');
    assert.strictEqual(quickPick.items[1].label, 'Not implemented yet');
  });
});
