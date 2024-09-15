import * as vscode from 'vscode';
import {
  Theme,
  ThemeQuickPickItem,
  ThemeFile,
  ThemeCategoryQuickPickItem,
  Action,
  ThemeFileQuickPickItem,
  SearchQuickPickItem,
} from '../types';
import alignText from '../utils/alignText';

export function createCategoryQuickPick(): vscode.QuickPick<ThemeCategoryQuickPickItem> {
  const quickPick = vscode.window.createQuickPick<ThemeCategoryQuickPickItem>();
  const labels = [
    {
      label: '$(star-full) By Rating | You can find most interesting themes here',
      description: '12.4K themes',
      theme_list_file: 'byrating',
    },
    {
      label: '$(arrow-up) Trending Weekly | A bit more interesting than most installed',
      description: '',
      theme_list_file: 'trendingweekly',
    },
    {
      label: '$(package) Most Installed | Most installed but boring themes',
      description: '',
      theme_list_file: 'mostinstalled',
    },
    {
      label: '$(organization) Publisher | Find Themes by Publisher',
      description: '',
      theme_list_file: 'publisher',
    },
    {
      label: '$(calendar) Published Date | Find Themes by Published Date',
      description: '',
      theme_list_file: 'publisheddate',
    },
    {
      label: '$(sync) Update Date | Find Themes by Update Date',
      description: '',
      theme_list_file: 'updatedate',
    },
    {
      label: '$(symbol-key) Sorted by Name | Find Themes by Name',
      description: '',
      theme_list_file: 'byname',
    },
    {
      label: '$(search) Search Themes | Search themes by name',
      description: '',
      theme_list_file: null,
      action: Action.SEARCH_THEMES,
    },
  ];

  quickPick.items = alignText(labels);
  quickPick.placeholder = 'Select a category';
  quickPick.step = 1;
  quickPick.totalSteps = 3;
  quickPick.title = 'Step 1/3: Select a category';
  return quickPick;
}

export function createThemeQuickPick(themes: Theme[]): vscode.QuickPick<ThemeQuickPickItem> {
  const quickPick = vscode.window.createQuickPick<ThemeQuickPickItem>();
  const goBackItem = alignText([
    {
      label: '$(arrow-left) Go Back | Return to category selection',
      description: '',
      action: Action.GO_BACK,
    },
  ]);

  quickPick.items = [
    ...goBackItem,
    ...themes.map((theme) => ({
      label: theme.displayName,
      description: `${theme.theme_files.length} ${theme.theme_files.length > 1 ? 'Themes' : 'Theme'}`,
      theme: theme,
    })),
  ];
  quickPick.placeholder = 'Select a theme';
  quickPick.step = 2;
  quickPick.totalSteps = 3;
  quickPick.title = 'Step 2/2: Select a theme';
  return quickPick;
}

export function createFileQuickPick(theme: Theme): vscode.QuickPick<ThemeFileQuickPickItem> {
  const quickPick = vscode.window.createQuickPick<ThemeFileQuickPickItem>();
  const goBackItem = alignText([
    {
      label: '$(arrow-left) Go Back | Return to theme selection',
      description: '',
      action: Action.GO_BACK,
    },
  ]);
  quickPick.items = [
    ...goBackItem,
    ...(theme.theme_files || []).map((file: ThemeFile) => ({
      label: file.name,
      description: file.file,
    })),
  ];
  quickPick.step = 3;
  quickPick.totalSteps = 3;
  quickPick.title = 'Step 3/3: Select a theme file';
  quickPick.buttons = [vscode.QuickInputButtons.Back];
  return quickPick;
}

export function createSearchQuickPick(): vscode.QuickPick<SearchQuickPickItem> {
  const quickPick = vscode.window.createQuickPick<SearchQuickPickItem>();
  quickPick.items = alignText([
    {
      label: '$(arrow-left) Go Back | Return to category selection',
      description: '',
      action: Action.GO_BACK,
    },
    {
      label: 'Not implemented yet',
      description: '',
      action: Action.SEARCH_THEMES,
    },
  ]);
  quickPick.placeholder = 'Search themes';
  quickPick.step = 1;
  quickPick.totalSteps = 1;
  quickPick.title = 'Search themes';
  return quickPick;
}
