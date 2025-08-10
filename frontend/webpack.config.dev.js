const { merge } = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
  mode: 'development',
  devtool: 'inline-source-map',
  devServer: {
    liveReload: true,
    hot: true,
    open: true,
    static: ['./'],
    proxy: [
      {
        context: ['/api'],
        target: 'http://localhost:8000',
        pathRewrite: { '^/api': '' },
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
        onProxyReq: (proxyReq, req, res) => {
          console.log('Proxying request:', req.method, req.url, '→', proxyReq.path);
        },
        onProxyRes: (proxyRes, req, res) => {
          console.log('Received response:', proxyRes.statusCode, 'for', req.url);
        },
        onError: (err, req, res) => {
          console.error('Proxy error:', err);
        }
      }
    ],
  },
});
