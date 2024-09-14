import * as vscode from 'vscode';
import * as Sentry from '@sentry/node';
import { ThemeQuickPickItem } from '../types';
import { getThemes, fetchThemeFile } from '../services/themeService';
import { restoreOriginalConfigurations, updateConfigurations } from '../services/configurationService';
import { createThemeQuickPick, createFileQuickPick } from '../ui/quickPicks';

export function registerThemeSelectorCommand(context: vscode.ExtensionContext): vscode.Disposable {
  return vscode.commands.registerCommand('live-themes.logToConsole', async () => {
    try {
      const themes = await getThemes(context);
      const themeQuickPick = createThemeQuickPick(themes);

      themeQuickPick.onDidChangeActive(async (items) => {
        if (items.length > 0) {
          const activeItem = items[0];
          console.log(`[Live Themes] Active item changed: ${activeItem.label}`);

          themeQuickPick.busy = true;
          try {
            const firstThemeFile = activeItem.theme.theme_files[0];
            if (firstThemeFile) {
              const themeContent = await fetchThemeFile(firstThemeFile.file);
              await updateConfigurations(themeContent);
            }
          } catch (error) {
            console.error('[Live Themes] Error fetching theme file:', error);
            Sentry.captureException(error);
            restoreOriginalConfigurations();
          } finally {
            themeQuickPick.busy = false;
          }
        }
      });

      themeQuickPick.onDidHide(() => {
        restoreOriginalConfigurations();
      });

      themeQuickPick.onDidAccept(async () => {
        const selectedTheme = themeQuickPick.selectedItems[0];
        if (selectedTheme) {
          themeQuickPick.hide();
          const fileQuickPick = createFileQuickPick(selectedTheme.theme);

          fileQuickPick.onDidChangeActive(async (items) => {
            if (items.length > 0 && items[0].label !== '$(arrow-left) Go Back') {
              const activeItem = items[0];
              console.log(`[Live Themes] Active theme file changed: ${activeItem.label}`);

              fileQuickPick.busy = true;
              try {
                const themeContent = await fetchThemeFile(activeItem.description || '');
                await updateConfigurations(themeContent);
              } catch (error) {
                console.error('[Live Themes] Error fetching theme file:', error);
                Sentry.captureException(error);
                restoreOriginalConfigurations();
              } finally {
                fileQuickPick.busy = false;
              }
            }
          });

          fileQuickPick.onDidAccept(() => {
            const selectedFile = fileQuickPick.selectedItems[0];
            if (selectedFile.label === '$(arrow-left) Go Back') {
              fileQuickPick.hide();
              themeQuickPick.show();
            } else if (selectedFile) {
              const theme = selectedTheme.theme;
              vscode.commands.executeCommand('workbench.extensions.action.showExtensionsWithIds', [
                `${theme.publisher.publisherName}.${theme.extension.extensionName}`,
              ]);

              fileQuickPick.dispose();
              themeQuickPick.dispose();
              restoreOriginalConfigurations();
            }
          });

          fileQuickPick.onDidHide(() => {
            restoreOriginalConfigurations();
            themeQuickPick.show();
          });

          fileQuickPick.show();
        }
      });

      themeQuickPick.show();
    } catch (error) {
      Sentry.captureException(error);
      console.error('[Live Themes] An error occurred in the extension:', error);
      restoreOriginalConfigurations();
      vscode.window.showErrorMessage(
        'An error occurred in the Live Themes extension. Original configurations have been restored.',
      );
    }
  });
}
