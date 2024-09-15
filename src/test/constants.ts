import { Theme } from '../types';

export const mockTheme1: Theme = {
  categories: ['Test Category'],
  displayName: 'Test Theme',
  publisher: {
    displayName: 'Test Publisher',
    publisherName: 'test-publisher',
  },
  tags: ['test-tag'],
  extension: {
    extensionId: 'test-extension-id',
    extensionName: 'Test Extension',
    latestVersion: '1.0.0',
    downloadUrl: 'https://test-download-url.com',
  },
  theme_files: [
    { name: 'test-theme-file-1', file: 'test-theme-file-1' },
    { name: 'test-theme-file-2', file: 'test-theme-file-2' },
  ],
  vsix_path: 'test-vsix-path',
  theme_dir: 'test-theme-dir',
};

export const mockTheme2: Theme = {
  categories: ['Test Category'],
  displayName: 'Test Theme 2',
  publisher: {
    displayName: 'Test Publisher',
    publisherName: 'test-publisher',
  },
  tags: ['test-tag'],
  extension: {
    extensionId: 'test-extension-id',
    extensionName: 'Test Extension',
    latestVersion: '1.0.0',
    downloadUrl: 'https://test-download-url.com',
  },
  theme_files: [{ name: 'test-theme-file-3', file: 'test-theme-file-3' }],
  vsix_path: 'test-vsix-path',
  theme_dir: 'test-theme-dir',
};

export const mockThemes: Theme[] = [mockTheme1, mockTheme2];
