import * as assert from 'assert';

// You can import and use all API from the 'vscode' module
// as well as import your extension to test it
import * as vscode from 'vscode';
// import * as myExtension from '../extension';

suite('Extension Test Suite', () => {
  suiteTeardown(() => {
    vscode.window.showInformationMessage('All tests done!');
  });

  test('Sample test', () => {
    assert.strictEqual(-1, [1, 2, 3].indexOf(5));
    assert.strictEqual(-1, [1, 2, 3].indexOf(0));
  });

  // TODO: `npm run test` command is not working properly.
  // it throws error after finishing tests with success.

  // Extension host with pid 30574 exited with code: 0, signal: unknown.
  // [UtilityProcessWorker]: terminated unexpectedly with code 1873934144, signal: unknown
});
