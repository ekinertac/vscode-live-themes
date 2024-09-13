import * as vscode from 'vscode';
import axios from 'axios';
import { Theme } from '../types';
import stripJsonComments from '../utils/strip-json-comments';

const THEMES_CACHE_KEY = 'liveThemes.cachedThemes';
const axiosClient = axios.create({
  baseURL: 'https://vscode-live-themes.ekinertac.com',
});

async function fetchThemes(): Promise<Theme[]> {
  const response = await axiosClient.get('/themes/list.json');
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

export async function getThemes(context: vscode.ExtensionContext): Promise<Theme[]> {
  const cachedData = context.globalState.get<{ themes: Theme[]; timestamp: number }>(THEMES_CACHE_KEY);
  const now = Date.now();

  if (cachedData && now - cachedData.timestamp < 24 * 60 * 60 * 1000) {
    return cachedData.themes;
  }

  const themes = await fetchThemes();
  await context.globalState.update(THEMES_CACHE_KEY, { themes, timestamp: now });
  return themes;
}
