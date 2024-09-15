import * as vscode from 'vscode';
import * as Sentry from '@sentry/node';
import { Action, ThemeQuickPickItem } from '../types';
import { getThemes, fetchThemeFile } from '../services/themeService';
import { restoreOriginalConfigurations, updateConfigurations } from '../services/configurationService';
import { createThemeQuickPick, createFileQuickPick, createCategoryQuickPick } from '../ui/quickPicks';

function handleThemeQuickPickEvents(themeQuickPick: vscode.QuickPick<ThemeQuickPickItem>) {
  themeQuickPick.onDidChangeActive(async (items) => {
    if (items.length > 0 && items[0].theme) {
      const activeItem = items[0];
      console.log(`[Live Themes] Active item changed: ${activeItem.label}`);

      themeQuickPick.busy = true;
      try {
        const firstThemeFile = activeItem.theme?.theme_files[0];
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
}

function handleFileQuickPickEvents(
  fileQuickPick: vscode.QuickPick<vscode.QuickPickItem>,
  themeQuickPick: vscode.QuickPick<ThemeQuickPickItem>,
  selectedTheme: ThemeQuickPickItem,
) {
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
        `${theme?.publisher.publisherName}.${theme?.extension.extensionName}`,
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
}

export function registerThemeSelectorCommand(context: vscode.ExtensionContext): vscode.Disposable {
  return vscode.commands.registerCommand('live-themes.selectTheme', async () => {
    try {
      const categoryQuickPick = createCategoryQuickPick();
      let lastActiveCategoryItem: vscode.QuickPickItem | undefined;

      categoryQuickPick.onDidChangeActive((items) => {
        if (items.length > 0) {
          lastActiveCategoryItem = items[0];
        }
      });

      categoryQuickPick.show();

      categoryQuickPick.onDidAccept(async () => {
        const selectedCategory = categoryQuickPick.selectedItems[0];
        if (selectedCategory) {
          categoryQuickPick.hide();

          const themes = await getThemes(context, selectedCategory.theme_list_file || '');
          const themeQuickPick = createThemeQuickPick(themes);

          handleThemeQuickPickEvents(themeQuickPick);

          themeQuickPick.onDidAccept(async () => {
            const selectedTheme = themeQuickPick.selectedItems[0];
            if (selectedTheme.action === Action.GO_BACK) {
              themeQuickPick.hide();
              // Update the items and restore the last active item
              categoryQuickPick.items = [...categoryQuickPick.items];
              if (lastActiveCategoryItem) {
                categoryQuickPick.activeItems = [lastActiveCategoryItem];
              }
              categoryQuickPick.show();
              return;
            }

            if (selectedTheme && selectedTheme.theme) {
              themeQuickPick.hide();
              const fileQuickPick = createFileQuickPick(selectedTheme.theme);
              fileQuickPick.title = `Step 2/3: ${selectedTheme.theme.displayName}`;
              handleFileQuickPickEvents(fileQuickPick, themeQuickPick, selectedTheme);

              fileQuickPick.show();
            }
          });

          themeQuickPick.show();
        }
      });
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
