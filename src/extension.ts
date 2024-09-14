import * as vscode from 'vscode';
import { registerThemeSelectorCommand } from './commands/themeSelector';
import * as Sentry from '@sentry/node';

export function activate(context: vscode.ExtensionContext) {
  Sentry.init({
    dsn: 'https://a7f5a48af43cecc6ed10281e52b0ebcb@o352105.ingest.us.sentry.io/4507953095245824',
  });

  console.log('Congratulations, your extension "live-themes" is now active!');
  const disposable = registerThemeSelectorCommand(context);

  context.subscriptions.push(disposable);
}

export function deactivate() {}
