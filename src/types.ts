import * as vscode from 'vscode';

export interface ThemeCache {
  themes: Theme[];
  timestamp: number;
}

export interface Theme {
  categories: string[];
  displayName: string;
  publisher: {
    displayName: string;
    publisherName: string;
  };
  tags: string[];
  extension: {
    extensionId: string;
    extensionName: string;
    latestVersion: string;
    downloadUrl: string;
  };
  theme_files: ThemeFile[];
  vsix_path: string;
  theme_dir: string;
}

export interface ThemeFile {
  name: string;
  file: string;
}

export const Action = {
  GO_BACK: 'go-back',
  SELECT_THEME: 'select-theme',
  SELECT_CATEGORY: 'select-category',
  SELECT_FILE: 'select-file',
};

export interface ThemeCategoryQuickPickItem extends vscode.QuickPickItem {
  theme_list_file: string | null;
  action?: string;
}
export interface ThemeQuickPickItem extends vscode.QuickPickItem {
  theme?: Theme;
  action?: string;
}

export interface ThemeFileQuickPickItem extends vscode.QuickPickItem {
  theme_file?: ThemeFile;
  action?: string;
}
