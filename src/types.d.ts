import * as vscode from 'vscode';

declare interface ThemeFile {
  file: string;
  name: string;
}

declare interface Theme {
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

declare interface ThemeQuickPickItem extends vscode.QuickPickItem {
  theme: Theme;
}
