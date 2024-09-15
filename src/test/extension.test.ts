import * as assert from 'assert';
import * as vscode from 'vscode';
import * as sinon from 'sinon';
import axios from 'axios';

suite('Extension Test Suite', () => {
  test('selectTheme command shows progress and multi-step quick pick', async () => {
    const mockThemes = [
      {
        displayName: 'Theme 1',
        theme_files: [
          { name: 'Light', file: 'https://example.com/theme1_light.json' },
          { name: 'Dark', file: 'https://example.com/theme1_dark.json' },
        ],
      },
      {
        displayName: 'Theme 2',
        theme_files: [{ name: 'Default', file: 'https://example.com/theme2.json' }],
      },
    ];

    // Mock axios.get
    const axiosStub = sinon.stub(axios, 'get');
    axiosStub.withArgs('https://vscode-live-themes.ekinertac.com/themes/list.json').resolves({ data: mockThemes });
    axiosStub.withArgs('https://example.com/theme1_light.json').resolves({ data: '{"theme": "content"}' });

    // Mock vscode.window.createQuickPick
    const quickPickStub = sinon.stub(vscode.window, 'createQuickPick').returns({
      items: [],
      placeholder: '',
      busy: false,
      onDidChangeActive: sinon.stub(),
      onDidAccept: sinon.stub(),
      show: sinon.stub(),
      hide: sinon.stub(),
      selectedItems: [{ label: 'Theme 1', description: '2 Themes', theme: mockThemes[0] }],
    });

    // Mock vscode.window.withProgress
    const withProgressStub = sinon.stub(vscode.window, 'withProgress').callsFake(async (options: any, task: any) => {
      await task({ report: sinon.stub() });
    });

    // Mock vscode.window.showQuickPick for the second step
    const showQuickPickStub = sinon.stub(vscode.window, 'showQuickPick').resolves({
      label: 'Light',
      description: 'https://example.com/theme1_light.json',
    });

    // Mock console.log
    const consoleLogSpy = sinon.spy(console, 'log');

    // Mock vscode.workspace.getConfiguration
    const getConfigurationStub = sinon.stub(vscode.workspace, 'getConfiguration');
    const editorConfigStub = {
      get: sinon.stub().returns({ originalTokenColors: 'value' }),
      update: sinon.stub().resolves(),
    };
    const workbenchConfigStub = {
      get: sinon.stub().returns({ originalColors: 'value' }),
      update: sinon.stub().resolves(),
    };
    getConfigurationStub.withArgs('editor').returns(editorConfigStub);
    getConfigurationStub.withArgs('workbench').returns(workbenchConfigStub);

    // Execute the command
    await vscode.commands.executeCommand('live-themes.selectTheme');

    // Simulate onDidChangeActive
    const createdQuickPick = quickPickStub.returnValues[0];
    await createdQuickPick.onDidChangeActive.args[0][0]([
      { label: 'Theme 1', description: '2 Themes', theme: mockThemes[0] },
    ]);

    // Simulate onDidHide
    createdQuickPick.onDidHide.args[0][0]();

    // Assert
    assert.strictEqual(axiosStub.callCount, 3); // Once for theme list, once for theme file, once for selected file
    assert.strictEqual(quickPickStub.callCount, 1);
    assert.strictEqual(withProgressStub.callCount, 1);
    assert.strictEqual(showQuickPickStub.callCount, 1);
    assert.strictEqual(showQuickPickStub.firstCall.args[0].length, 2);
    assert(consoleLogSpy.calledWith('Active item changed: Theme 1'));
    assert(consoleLogSpy.calledWith('Fetched theme file: Light'));
    assert(consoleLogSpy.calledWith('Selected theme file: Light (https://example.com/theme1_light.json)'));
    assert(editorConfigStub.get.calledWith('tokenColorCustomizations'));
    assert(workbenchConfigStub.get.calledWith('colorCustomizations'));
    assert.strictEqual(editorConfigStub.update.callCount, 2);
    assert.strictEqual(workbenchConfigStub.update.callCount, 2);

    // Restore mocks
    axiosStub.restore();
    quickPickStub.restore();
    withProgressStub.restore();
    showQuickPickStub.restore();
    consoleLogSpy.restore();
    getConfigurationStub.restore();
  });
});
