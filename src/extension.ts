import * as vscode from 'vscode';
import { registerThemeSelectorCommand } from './commands/themeSelector';

export function activate(context: vscode.ExtensionContext) {
  console.log('Congratulations, your extension "live-themes" is now active!');

  const disposable = registerThemeSelectorCommand(context);
  context.subscriptions.push(disposable);
}

export function deactivate() {}
