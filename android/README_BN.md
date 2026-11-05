# RB Portfolio — অ্যাপ হিসেবে ব্যবহার (বাংলা গাইড)

পোর্টফোলিও সাইট <https://rbchy.github.io/rbchy/> এখন একটা **অ্যাপ** হিসেবে চলে:

| প্ল্যাটফর্ম | কীভাবে | কী লাগবে |
|---|---|---|
| Android (Chrome) | সাইট খুলে উপরের **Install app** বোতাম, বা মেনু → *Install app* | কিছুই না |
| iPhone / iPad (Safari) | Share বোতাম → **Add to Home Screen** (সাইটেই টিপস দেখায়) | কিছুই না |
| Windows / Mac (Chrome, Edge) | ঠিকানা-বারের পাশে install আইকন, বা **Install app** বোতাম | কিছুই না |
| Android APK / Play Store | নিচের GitHub Actions ধাপ | Play Store-এর জন্য $25 এককালীন |

অ্যাপটা অফলাইনেও খোলে (শেষবার দেখা পাতা, নইলে একটা ছোট অফলাইন পাতা)।

## ফাইলগুলো কী করে

- `manifest.webmanifest` — অ্যাপের নাম, আইকন, রং, শর্টকাট (Shop, Projects, Contact)।
- `sw.js` — service worker; পাতা ক্যাশে রাখে, অফলাইনে চালায়।
- `offline.html` — নেট না থাকলে দেখানোর পাতা।
- `app/` — আইকন (সাধারণ, maskable, Apple, favicon)।
- `android/build-twa.mjs` — Bubblewrap দিয়ে সাইটটাকে Android অ্যাপে (Trusted Web Activity) মোড়ে।
- `.github/workflows/android-app.yml` — APK আর AAB বানায়।

> সাইটে কিছু বদলালে অ্যাপ নতুন করে বানাতে হয় না — অ্যাপ সবসময় লাইভ সাইট দেখায়।
> শুধু `sw.js`-এর `VERSION` এক ধাপ বাড়ালে পুরোনো ক্যাশ মুছে যায়।

## ধাপ ১ — APK বানানো (এখনই করা যায়)

1. GitHub → **rbchy/rbchy** → **Actions** → *build Android app (TWA)* → **Run workflow**।
2. শেষ হলে নিচে **rb-portfolio-android** artifact নামাও। ভেতরে:
   - `rb-portfolio.apk` — ফোনে সরাসরি ইনস্টল (Unknown sources চালু করতে হবে)।
   - `rb-portfolio.aab` — Play Console-এ আপলোডের জন্য।
   - `assetlinks.json` — ধাপ ৩-এর জন্য।

secret না থাকলে প্রতি রানে **নতুন অস্থায়ী key** দিয়ে সাইন হয় — পরীক্ষার জন্য ঠিক আছে,
কিন্তু Play Store-এ দেওয়ার আগে ধাপ ২ করো।

## ধাপ ২ — স্থায়ী signing key (একবারই)

নিজের কম্পিউটারে (Java থাকলে):

```bash
keytool -genkeypair -keystore portfolio.keystore -alias portfolio \
  -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=RB Chowdhury, O=rbchy, C=BD"
base64 -w0 portfolio.keystore > keystore.b64     # Mac: base64 -i portfolio.keystore
```

GitHub → rbchy/rbchy → **Settings → Secrets and variables → Actions → New repository secret**:

| নাম | মান |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | `keystore.b64`-এর পুরো লেখা |
| `ANDROID_KEYSTORE_PASSWORD` | keystore পাসওয়ার্ড |
| `ANDROID_KEY_ALIAS` | `portfolio` |
| `ANDROID_KEY_PASSWORD` | key পাসওয়ার্ড (একই হলে একই দাও) |

⚠️ `portfolio.keystore` আর পাসওয়ার্ড নিরাপদে রাখো — হারালে Play Store-এ অ্যাপ আপডেট করা যাবে না।
এটা কখনো repo-তে commit করবে না।

## ধাপ ৩ — URL-বার ছাড়া পুরো-স্ক্রিন (Digital Asset Links)

অ্যাপ এখনই চলে, কিন্তু উপরে একটা ছোট URL-বার দেখায়, যতক্ষণ না Android প্রমাণ পায় যে
সাইট আর অ্যাপ একই মালিকের। ফাইলটা থাকতে হয় **ডোমেনের মূলে**:
`https://rbchy.github.io/.well-known/assetlinks.json` — তাই একটা আলাদা repo লাগবে:

1. GitHub-এ নতুন **public** repo বানাও, নাম ঠিক **`rbchy.github.io`**।
2. তাতে দুটো ফাইল যোগ করো:
   - `.nojekyll` (খালি ফাইল — নইলে `.well-known` ফোল্ডার প্রকাশ হয় না)
   - `.well-known/assetlinks.json` — workflow থেকে পাওয়া ফাইলটা হুবহু।
3. Settings → Pages → *Deploy from a branch* → `main` / root।
4. Play Store-এ দিলে Play Console → *App integrity* → **App signing key**-এর SHA-256-ও
   `sha256_cert_fingerprints` তালিকায় যোগ করো (Google নিজের key দিয়ে আবার সাইন করে)।

পরীক্ষা: <https://developers.google.com/digital-asset-links/tools/generator>

ℹ️ নতুন repo বানালে `rbchy.github.io` মূল ঠিকানায় সেই repo-র পাতা দেখাবে; `/rbchy/` পোর্টফোলিও আগের মতোই থাকবে।
চাইলে মূল পাতায় একটা `index.html` রেখে `/rbchy/`-এ পাঠিয়ে দিতে পারো।

## ধাপ ৪ — Google Play Store

1. <https://play.google.com/console> — ডেভেলপার অ্যাকাউন্ট ($25, একবার)।
2. *Create app* → নাম "RB Portfolio" → `rb-portfolio.aab` আপলোড।
3. স্টোর লিস্টিং: আইকন (`android/build/store_icon.png` বা `app/icon-512.png`), স্ক্রিনশট, বিবরণ, privacy policy লিংক।
4. নতুন ব্যক্তিগত অ্যাকাউন্টে আগে **closed testing** (১২ জন টেস্টার, ১৪ দিন) লাগে, তারপর production।
5. প্রতিটা নতুন আপলোডে workflow চালানোর সময় `version_code` এক বাড়াও।

## iPhone App Store কেন এখন নয়

শুধু একটা ওয়েবসাইট মোড়ানো অ্যাপ Apple সাধারণত **guideline 4.2 (Minimum Functionality)**-এ বাতিল করে,
আর ডেভেলপার অ্যাকাউন্ট $99/বছর। iPhone-এ তাই এখন **Add to Home Screen** সবচেয়ে ভালো পথ —
আইকন, পুরো-স্ক্রিন আর অফলাইন সবই পায়। পরে নিজস্ব ফিচার (notification, অফলাইন ক্যাটালগ ইত্যাদি)
যোগ হলে Capacitor দিয়ে iOS অ্যাপ ভাবা যাবে।
