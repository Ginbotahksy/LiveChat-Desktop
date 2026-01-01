const webpack = require('webpack');

module.exports = {
  packagerConfig: {
    extendInfo: {
      LSUIElement: "1", // Mode agent pour macOS
    },
  },
  rebuildConfig: {},
  makers: [
    { name: '@electron-forge/maker-squirrel' },
    { name: '@electron-forge/maker-zip', platforms: ['darwin'] },
    { name: '@electron-forge/maker-deb', config: {} },
    { name: '@electron-forge/maker-rpm', config: {} },
  ],
  plugins: [
    {
      name: '@electron-forge/plugin-webpack',
      config: {
        mainConfig: {
          entry: './src/main.js',
          target: 'electron-main',
          plugins: [
            new webpack.DefinePlugin({
              'process.env.ADDRESS': JSON.stringify(process.env.ADDRESS),
            }),
          ],
        },
        renderer: {
          config: {
            entry: './src/renderer.js',
            target: 'electron-renderer',
            plugins: [
              new webpack.DefinePlugin({
                'process.env.ADDRESS': JSON.stringify(process.env.ADDRESS),
              }),
            ],
          },
          entryPoints: [
            {
              html: './src/index.html',
              js: './src/renderer.js',
              name: 'main_window',
            },
          ],
        },
      },
    },
  ],
};