import * as vscode from 'vscode';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { Theme } from '../types';
import stripJsonComments from '../utils/strip-json-comments';

// Add this function to check if we're in development mode
const __DEV__ = process.env.VSCODE_DEBUG_MODE === 'true';

const THEMES_CACHE_KEY = 'liveThemes.cachedThemes';
const axiosClient = axios.create({
  baseURL: __DEV__ ? 'http://localhost:9000' : 'https://vscode-live-themes.ekinertac.com',
});

async function fetchThemes(theme_list_file: string): Promise<Theme[]> {
  const response = await axiosClient.get(`/themes/${theme_list_file}.json`);
  return response.data;
}

export async function fetchThemeFile(fileUrl: string): Promise<any> {
  const response = await axiosClient.get(fileUrl);
  if (typeof response.data === 'string') {
    const themeContentObj = JSON.parse(stripJsonComments(response.data, { trailingCommas: true }));
    return themeContentObj;
  }
  return response.data;
}

export async function getThemes(context: vscode.ExtensionContext, theme_list_file: string): Promise<Theme[]> {
  if (!__DEV__) {
    const cachedData = context.globalState.get<{ themes: Theme[]; timestamp: number }>(THEMES_CACHE_KEY);
    const now = Date.now();

    if (cachedData && now - cachedData.timestamp < 24 * 60 * 60 * 1000) {
      return cachedData.themes;
    }
  }

  const themes = await fetchThemes(theme_list_file);

  if (!__DEV__) {
    await context.globalState.update(THEMES_CACHE_KEY, { themes, timestamp: Date.now() });
  }

  return themes;
}
