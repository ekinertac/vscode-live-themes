import * as vscode from 'vscode';
import axios from 'axios';
import { ThemeQuickPickItem, Theme, ThemeFile } from './types';
import stripJsonComments from './utils/strip-json-comments';

let originalTokenColors: any;
let originalColors: any;
let cachedThemes: Theme[] = [];

// Cache key for themes
const THEMES_CACHE_KEY = 'liveThemes.cachedThemes';

function restoreOriginalConfigurations() {
  vscode.workspace
    .getConfiguration('editor')
    .update('tokenColorCustomizations', originalTokenColors, vscode.ConfigurationTarget.Workspace);
  vscode.workspace
    .getConfiguration('workbench')
    .update('colorCustomizations', originalColors, vscode.ConfigurationTarget.Workspace);
}

export function activate(context: vscode.ExtensionContext) {
  console.log('Congratulations, your extension "live-themes" is now active!');

  let disposable = vscode.commands.registerCommand('live-themes.logToConsole', async () => {
    console.log('[Live Themes] Hello from Live Themes extension!');

    try {
      // Backup original configurations
      originalTokenColors = vscode.workspace.getConfiguration('editor').get('tokenColorCustomizations');
      originalColors = vscode.workspace.getConfiguration('workbench').get('colorCustomizations');

      const quickPick = vscode.window.createQuickPick<ThemeQuickPickItem>();
      quickPick.placeholder = 'Loading themes...';
      quickPick.busy = true;
      quickPick.show();

      await vscode.window.withProgress(
        {
          location: { viewId: 'quickPick' },
          title: 'Fetching themes...',
          cancellable: false,
        },
        async (progress) => {
          progress.report({ increment: 0 });
          cachedThemes = await getThemes(context);
          progress.report({ increment: 100 });
        },
      );

      quickPick.step = 1;
      quickPick.totalSteps = 2;
      quickPick.title = 'Step 1/2: Select a theme';

      function updateQuickPickItems() {
        quickPick.items = cachedThemes.map((theme) => ({
          label: theme.displayName,
          description: `${theme.theme_files.length} ${theme.theme_files.length > 1 ? 'Themes' : 'Theme'}`,
          theme: theme,
        }));
      }

      updateQuickPickItems();

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
                .update(
                  'tokenColorCustomizations',
                  { textMateRules: tokenColors },
                  vscode.ConfigurationTarget.Workspace,
                );
              await vscode.workspace
                .getConfiguration('workbench')
                .update('colorCustomizations', colors, vscode.ConfigurationTarget.Workspace);
            }
          } catch (error) {
            console.error('Error fetching theme file:', error);
            restoreOriginalConfigurations();
          } finally {
            quickPick.busy = false;
          }
        }
      });

      quickPick.onDidHide(() => {
        restoreOriginalConfigurations();
      });

      quickPick.onDidAccept(async () => {
        const selectedTheme = quickPick.selectedItems[0];
        if (selectedTheme) {
          quickPick.hide();

          const fileQuickPick = vscode.window.createQuickPick();
          const goBackItem = { label: '$(arrow-left) Go Back', description: '  Return to theme selection' };
          fileQuickPick.items = [
            goBackItem,
            ...selectedTheme.theme.theme_files.map((file: ThemeFile) => ({
              label: file.name,
              description: file.file,
            })),
          ];

          fileQuickPick.step = 2;
          fileQuickPick.totalSteps = 2;
          fileQuickPick.title = 'Step 2/2: Select a theme file';

          function goBack() {
            fileQuickPick.hide();
            updateQuickPickItems();
            quickPick.show();
          }

          fileQuickPick.onDidChangeActive(async (items) => {
            if (items.length > 0 && items[0] !== goBackItem) {
              const activeItem = items[0];
              console.log(`Active theme file changed: ${activeItem.label}`);

              fileQuickPick.busy = true;
              try {
                const themeContent = await fetchThemeFile(activeItem.description || '');
                const tokenColors = themeContent.tokenColors;
                const colors = themeContent.colors;

                await vscode.workspace
                  .getConfiguration('editor')
                  .update(
                    'tokenColorCustomizations',
                    { textMateRules: tokenColors },
                    vscode.ConfigurationTarget.Workspace,
                  );
                await vscode.workspace
                  .getConfiguration('workbench')
                  .update('colorCustomizations', colors, vscode.ConfigurationTarget.Workspace);
              } catch (error) {
                console.error('Error fetching theme file:', error);
                restoreOriginalConfigurations();
              } finally {
                fileQuickPick.busy = false;
              }
            }
          });

          fileQuickPick.onDidAccept(() => {
            const selectedFile = fileQuickPick.selectedItems[0];
            if (selectedFile === goBackItem) {
              goBack();
            } else if (selectedFile) {
              //MARK: Final select
              const theme = selectedTheme.theme;
              // vscode.commands.executeCommand(
              // 'workbench.extensions.installExtension',
              // `${theme.publisher.publisherName}.${theme.extension.extensionName}`,
              // );

              vscode.commands.executeCommand('workbench.extensions.action.showExtensionsWithIds', [
                `${theme.publisher.publisherName}.${theme.extension.extensionName}`,
              ]);

              fileQuickPick.dispose();
              quickPick.dispose();
              restoreOriginalConfigurations();
            }
          });

          fileQuickPick.onDidHide(() => {
            restoreOriginalConfigurations();
            updateQuickPickItems(); // Update items when returning to the first QuickPick
            quickPick.show();
          });

          // Add back button functionality
          fileQuickPick.buttons = [vscode.QuickInputButtons.Back];
          fileQuickPick.onDidTriggerButton((button) => {
            if (button === vscode.QuickInputButtons.Back) {
              goBack();
            }
          });

          fileQuickPick.show();
        }
      });
    } catch (error) {
      console.error('An error occurred in the extension:', error);
      restoreOriginalConfigurations();
      vscode.window.showErrorMessage(
        'An error occurred in the Live Themes extension. Original configurations have been restored.',
      );
    }
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

async function getThemes(context: vscode.ExtensionContext): Promise<Theme[]> {
  const cachedData = context.globalState.get<{ themes: Theme[]; timestamp: number }>(THEMES_CACHE_KEY);
  const now = Date.now();

  if (cachedData && now - cachedData.timestamp < 24 * 60 * 60 * 1000) {
    // Use cached data if it's less than a day old
    return cachedData.themes;
  }

  // Fetch new data
  const themes = await fetchThemes();

  // Cache the new data
  await context.globalState.update(THEMES_CACHE_KEY, { themes, timestamp: now });

  return themes;
}

export function deactivate() {}
