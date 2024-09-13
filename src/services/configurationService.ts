import * as vscode from 'vscode';

let originalTokenColors: any;
let originalColors: any;

export function backupOriginalConfigurations() {
  originalTokenColors = vscode.workspace.getConfiguration('editor').get('tokenColorCustomizations');
  originalColors = vscode.workspace.getConfiguration('workbench').get('colorCustomizations');
}

export function restoreOriginalConfigurations() {
  vscode.workspace
    .getConfiguration('editor')
    .update('tokenColorCustomizations', originalTokenColors, vscode.ConfigurationTarget.Workspace);
  vscode.workspace
    .getConfiguration('workbench')
    .update('colorCustomizations', originalColors, vscode.ConfigurationTarget.Workspace);
}

export async function updateConfigurations(themeContent: any) {
  const tokenColors = themeContent.tokenColors;
  const colors = themeContent.colors;

  await vscode.workspace
    .getConfiguration('editor')
    .update('tokenColorCustomizations', { textMateRules: tokenColors }, vscode.ConfigurationTarget.Workspace);
  await vscode.workspace
    .getConfiguration('workbench')
    .update('colorCustomizations', colors, vscode.ConfigurationTarget.Workspace);
}
