const webpack = require('webpack');

module.exports = {
  // ... packagerConfig
  plugins: [
    {
      name: '@electron-forge/plugin-webpack',
      config: {
        mainConfig: {
          entry: './src/main.js',
          plugins: [
            new webpack.DefinePlugin({
              'process.env.ADDRESS': JSON.stringify(process.env.ADDRESS)
            })
          ],
        },
        renderer: {
          config: {
            entry: './src/renderer.js',
            plugins: [
              new webpack.DefinePlugin({
                'process.env.ADDRESS': JSON.stringify(process.env.ADDRESS)
              })
            ]
          },
        }
      }
    }
  ]
};