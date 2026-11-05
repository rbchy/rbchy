/*
 * Generates the Android app (a Trusted Web Activity: the portfolio site in full screen, from Chrome) without any
 * questions, so CI can build it. Uses Google's Bubblewrap library.
 *
 *   node android/build-twa.mjs <outDir> [iconBase]
 *
 * The site, start page and scope come from manifest.webmanifest in this repository. The icons are read from iconBase
 * (default: the live site), so CI can build from the files of a pull request before they are published.
 * Version: APP_VERSION_CODE (CI run number) and APP_VERSION_NAME.
 */
import { readFile } from 'node:fs/promises';
import { TwaManifest, TwaGenerator, ConsoleLog } from '@bubblewrap/core';

const SITE = 'https://rbchy.github.io/rbchy/';
const [outDir = 'android/build', iconBase = SITE] = process.argv.slice(2);

const web = JSON.parse(await readFile(new URL('../manifest.webmanifest', import.meta.url), 'utf8'));
const twa = TwaManifest.fromWebManifestJson(new URL('manifest.webmanifest', SITE), web);

twa.packageId = 'io.github.rbchy.portfolio';
twa.name = web.name;
twa.launcherName = web.short_name;
twa.startUrl = '/rbchy/?source=android';
twa.iconUrl = new URL('app/icon-512.png', iconBase).toString();
twa.maskableIconUrl = new URL('app/icon-maskable-512.png', iconBase).toString();
twa.webManifestUrl = new URL('manifest.webmanifest', iconBase);       // copied into the app for ChromeOS
// colours (theme, navigation bar, splash background) come from the web manifest
twa.fallbackType = 'customtabs';
twa.enableNotifications = false;
twa.signingKey = { path: './portfolio.keystore', alias: 'portfolio' };
twa.appVersionCode = Number(process.env.APP_VERSION_CODE || 1);
twa.appVersionName = process.env.APP_VERSION_NAME || `1.0.${twa.appVersionCode}`;
twa.generatorApp = 'rbchy/android/build-twa.mjs';
// shortcuts use the same icon as the app
for (const s of twa.shortcuts) s.chosenIconUrl = twa.iconUrl;

const errors = twa.validate ? twa.validate() : null;
if (errors) { console.error('twa-manifest:', errors); process.exit(1); }

await new TwaGenerator().createTwaProject(outDir, twa, new ConsoleLog('twa'));
console.log(`Generated ${twa.packageId} ${twa.appVersionName} (${twa.appVersionCode}) for ${twa.host}${twa.startUrl} in ${outDir}`);
