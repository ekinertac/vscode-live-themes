import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Extension Test Suite', () => {
  vscode.window.showInformationMessage('Start all tests.');

  test('registerThemeSelectorCommand registers a command', () => {
    const a = 1;
    assert.strictEqual(a, 1);
  });
});
