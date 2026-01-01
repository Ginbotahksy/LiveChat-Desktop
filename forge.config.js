const webpack = require('webpack'); // N'oublie pas l'import en haut

module.exports = {
  // ... tes autres configs (packagerConfig, etc.)
  plugins: [
    {
      name: '@electron-forge/plugin-webpack',
      config: {
        mainConfig: {
          entry: '.main.js',
          module: {
            rules: [/* ... */]
          },
          plugins: [
            // C'est ICI qu'on injecte les variables du workflow
            new webpack.DefinePlugin({
              'process.env.SOCKET_URL': JSON.stringify(process.env.SOCKET_URL),
              'process.env.API_KEY': JSON.stringify(process.env.API_KEY),
            })
          ]
        },
        renderer: {
          config: {
            entry: './src/renderer.js',
            plugins: [
                new webpack.DefinePlugin({
                  'process.env.SOCKET_URL': JSON.stringify(process.env.SOCKET_URL),
                })
              ]
          },
          entryPoints: [
            {
              html: './src/index.html',
              js: './src/renderer.js',
              name: 'main_window',
            }
          ]
        }
      }
    }
  ]
};