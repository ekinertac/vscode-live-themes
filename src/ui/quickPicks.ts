import * as vscode from 'vscode';
import { Theme, ThemeQuickPickItem, ThemeFile } from '../types';

export function createThemeQuickPick(themes: Theme[]): vscode.QuickPick<ThemeQuickPickItem> {
  const quickPick = vscode.window.createQuickPick<ThemeQuickPickItem>();
  quickPick.items = themes.map((theme) => ({
    label: theme.displayName,
    description: `${theme.theme_files.length} ${theme.theme_files.length > 1 ? 'Themes' : 'Theme'}`,
    theme: theme,
  }));
  quickPick.placeholder = 'Select a theme';
  quickPick.step = 1;
  quickPick.totalSteps = 2;
  quickPick.title = 'Step 1/2: Select a theme';
  return quickPick;
}

export function createFileQuickPick(theme: Theme): vscode.QuickPick<vscode.QuickPickItem> {
  const quickPick = vscode.window.createQuickPick();
  const goBackItem = { label: '$(arrow-left) Go Back', description: '  Return to theme selection' };
  quickPick.items = [
    goBackItem,
    ...(theme.theme_files || []).map((file: ThemeFile) => ({
      label: file.name,
      description: file.file,
    })),
  ];
  quickPick.step = 2;
  quickPick.totalSteps = 2;
  quickPick.title = 'Step 2/2: Select a theme file';
  quickPick.buttons = [vscode.QuickInputButtons.Back];
  return quickPick;
}
