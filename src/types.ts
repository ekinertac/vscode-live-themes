import * as vscode from 'vscode';

export interface ThemeCache {
  themes: Theme[];
  timestamp: number;
}

export interface Theme {
  displayName: string;
  theme_files: ThemeFile[];
  // Add other properties as needed
}

export interface ThemeFile {
  name: string;
  file: string;
  // Add other properties as needed
}

export interface ThemeQuickPickItem extends vscode.QuickPickItem {
  theme: Theme;
}
