import * as vscode from 'vscode';
import axios from 'axios';
import { ThemeQuickPickItem, Theme, ThemeFile } from './types';
import stripJsonComments from './utils/strip-json-comments';

let originalTokenColors: any;
let originalColors: any;

export function activate(context: vscode.ExtensionContext) {
  console.log('Congratulations, your extension "live-themes" is now active!');

  let disposable = vscode.commands.registerCommand('live-themes.logToConsole', async () => {
    console.log('[Live Themes] Hello from Live Themes extension!');

    const quickPick = vscode.window.createQuickPick<ThemeQuickPickItem>();
    quickPick.placeholder = 'Loading themes...';
    quickPick.busy = true;
    quickPick.show();

    let themes: Theme[] = [];

    await vscode.window.withProgress(
      {
        location: { viewId: 'quickPick' },
        title: 'Fetching themes...',
        cancellable: false,
      },
      async (progress) => {
        progress.report({ increment: 0 });
        themes = await fetchThemes();
        progress.report({ increment: 100 });
      },
    );

    quickPick.busy = false;
    quickPick.placeholder = 'Select a theme';
    quickPick.items = themes.map((theme) => ({
      label: theme.displayName,
      description: `${theme.theme_files.length} ${theme.theme_files.length > 1 ? 'Themes' : 'Theme'}`,
      theme: theme,
    }));

    // Backup original configurations
    originalTokenColors = vscode.workspace.getConfiguration('editor').get('tokenColorCustomizations');
    originalColors = vscode.workspace.getConfiguration('workbench').get('colorCustomizations');

    quickPick.onDidChangeActive(async (items) => {
      if (items.length > 0) {
        const activeItem = items[0];
        console.log(`Active item changed: ${activeItem.label}`);

        quickPick.busy = true;
        try {
          const firstThemeFile = activeItem.theme.theme_files[0];
          if (firstThemeFile) {
            const themeContent = await fetchThemeFile(firstThemeFile.file);
            const tokenColors = themeContent.tokenColors;
            const colors = themeContent.colors;
            await vscode.workspace
              .getConfiguration('editor')
              .update('tokenColorCustomizations', { textMateRules: tokenColors }, vscode.ConfigurationTarget.Global);
            await vscode.workspace
              .getConfiguration('workbench')
              .update('colorCustomizations', colors, vscode.ConfigurationTarget.Global);
          }
        } catch (error) {
          console.error('Error fetching theme file:', error);
        } finally {
          quickPick.busy = false;
        }
      }
    });

    quickPick.onDidHide(() => {
      // Restore original configurations
      vscode.workspace
        .getConfiguration('editor')
        .update('tokenColorCustomizations', originalTokenColors, vscode.ConfigurationTarget.Global);
      vscode.workspace
        .getConfiguration('workbench')
        .update('colorCustomizations', originalColors, vscode.ConfigurationTarget.Global);
    });

    quickPick.onDidAccept(async () => {
      const selectedTheme = quickPick.selectedItems[0];
      if (selectedTheme) {
        quickPick.hide();

        // Second step: Show theme files
        const selectedFile = await vscode.window.showQuickPick(
          selectedTheme.theme.theme_files.map((file: ThemeFile) => ({
            label: file.name,
            description: file.file,
          })),
          { placeHolder: 'Select a theme file' },
        );

        if (selectedFile) {
          console.log(`Selected theme file: ${selectedFile.label} (${selectedFile.description})`);
          // Here you can add logic to apply the selected theme file
        }
      }
    });
  });

  context.subscriptions.push(disposable);
}

const axiosClient = axios.create({
  baseURL: 'https://vscode-live-themes.ekinertac.com',
});

async function fetchThemes(): Promise<Theme[]> {
  const response = await axiosClient.get('/themes/list.json');
  return response.data;
}

async function fetchThemeFile(fileUrl: string): Promise<any> {
  const response = await axiosClient.get(fileUrl);
  // using eval to avoid JSON.parse syntax issues like comments, trailing commas, etc.
  if (typeof response.data === 'string') {
    const themeContentObj = JSON.parse(stripJsonComments(response.data, { trailingCommas: true }));
    return themeContentObj;
  }

  return response.data;
}

function cleanJson(jsonString: string) {
  jsonString = jsonString
    .replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '') // Remove comments (single-line and multi-line)
    .replace(/,\s*}/g, '}') // Remove trailing commas
    .replace(/,\s*]/g, ']') // Remove trailing commas
    .replace(/\n|\t|\r/g, ''); // Remove all new lines, tabs and carriage returns

  return jsonString;
}

export function deactivate() {}
