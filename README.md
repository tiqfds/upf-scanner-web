# Ultra-processed food scanner (web)

A Next.js app you can host on your own machine. It opens the camera on an ingredient label, collects a name and email in the browser session, and shows a short explanation of the NOVA groups.

This repository is the web client only, copied out of the product so it can be cloned and run by itself.

## Requirements

- Node.js 20 or newer
- npm

## Host it locally

```bash
npm install
npm run build
npm run start
```

Open [http://localhost:3000](http://localhost:3000).

`npm run start` serves the production build. While you are changing the UI, use `npm run dev` instead. That also serves [http://localhost:3000](http://localhost:3000) and reloads as you edit.

The camera needs permission in the browser. Sign-in with Apple or Google is not connected in this copy. The name and email stay in this browser tab.

## Stack

Next.js 16, React 19, TypeScript, and Tailwind CSS 4.
