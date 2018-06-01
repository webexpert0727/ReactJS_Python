'use strict';

const webpack = require('webpack');
const path = require('path');
const merge = require('webpack-merge');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const BundleTracker = require('webpack-bundle-tracker');
// const ChunkManifestPlugin = require('chunk-manifest-webpack-plugin');
const WebpackChunkHash = require('webpack-chunk-hash');

const __DEV__ = process.env.NODE_ENV !== 'production';
const __HOST__ = process.env.NODE_HOST || 'localhost';

function getEntrySources(entryName) {
  const sources = [];
  if (__DEV__) {
    sources.push(
     'react-hot-loader/patch',
     `webpack-dev-server/client?http://${__HOST__}:3000`,
     'webpack/hot/only-dev-server'
    );
  }
  sources.push(`./frontend/${entryName}/index.js`);
  return sources;
}

function getPlugins() {
  const plugins = [
    new webpack.EnvironmentPlugin('NODE_ENV'),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
    }),
    new webpack.DefinePlugin({
      STATIC: JSON.stringify('/static/'),
      __DEV__: __DEV__,
    }),
    new webpack.optimize.CommonsChunkPlugin({
      // only for client part, not for manager app
      names: ['common', 'vendor'],
      filename: __DEV__ ? 'app.[name].js' : 'app.[name].[chunkhash].js',
      chunks: ['common', 'app'],  // https://github.com/webpack/webpack/issues/4445
    }),
    new ExtractTextPlugin({
      filename: __DEV__ ? '[name].styles.css' : '[name].styles.[chunkhash].css',
      // allChunks: true,
    })
  ];
  if (__DEV__) {
    plugins.push(
      new webpack.HotModuleReplacementPlugin(),
      new webpack.NamedModulesPlugin()
    );
  } else {
    plugins.push(
      new webpack.NoEmitOnErrorsPlugin(),
      new WebpackChunkHash()
      /* not done yet

        - https://webpack.js.org/guides/caching/
        - https://github.com/owais/django-webpack-loader/issues/104

      new webpack.HashedModuleIdsPlugin(),
      new ChunkManifestPlugin({
        filename: '../../webpack.manifest.chunks.json',
      })

      */
    );
  }
  return plugins;
}

function getDevServerSetting() {
  if (__DEV__) {
    return {
      hot: true,
      host: '0.0.0.0',
      port: 3000,
      inline: true,
      contentBase: path.resolve(__dirname, 'static'),
      publicPath: '/static/dist/',
      historyApiFallback: true,
      // https://github.com/webpack/webpack-dev-server/issues/882
      disableHostCheck: true,
      proxy: {
        '/': 'http://localhost:8000/',
      },
    };
  }
  return {};
}


const baseConfig = {
  output: {
    path: path.resolve(__dirname, 'static/dist'),
    filename: __DEV__ ? '[name].bundle.js' : '[name].bundle.[chunkhash].js',
    publicPath: '/static/dist/',
  },
  devtool: __DEV__ ? 'cheap-module-eval-source-map' : false,
  devServer: getDevServerSetting(),
  module: {
    rules: [
      // {
      //   // FIXME: for the future ;)
      //   test: /\.(js|jsx)$/,
      //   enforce: 'pre',
      //   loader: 'eslint-loader',
      //   include: /src/
      // },
      {
        test: /\.(js|jsx)?$/,
        loader: 'babel-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        include: /node_modules/,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.css$/,
        exclude: /node_modules/,
        use: ExtractTextPlugin.extract({
          fallback: 'style-loader',
          use: [
            {
              loader: 'css-loader',
              options: {
                modules: true,
                importLoaders: 1,
                minimize: false,
                localIdentName: __DEV__ ? '[folder]__[local]' : '[hash:base64:5]',
              },
            },
            {
              loader: 'postcss-loader',
              options: {
                plugins: () => [
                  require('postcss-import'),
                  require('postcss-cssnext'),
                ],
              },
            },
          ],
        }),
      },
      {
        test: /\.scss$/,
        use: ExtractTextPlugin.extract({
          fallback: 'style-loader',
          use: ['css-loader', 'sass-loader'],
        }),
      },
      {
        test: /\.coffee$/,
        loader: 'coffee-loader',
      },
      {
        test: /\.(coffee\.md|litcoffee)$/,
        loader: 'coffee-loader?literate',
      },
      {
        test: /\.(jpe?g|png|gif|svg)$/i,
        use: [
          {
            loader: 'url-loader',
            options: {
              limit: 10000,
              name: 'images/[name].[ext]',
            },
          },
        ],
      },
      {
        test: /\.(eot|otf|ttf|woff|woff2)$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: 'fonts/[name].[ext]',
            },
          },
        ],
      },
    ],
  },
  plugins: getPlugins(),
  resolve: {
    extensions: ['.js', '.jsx', '.json', '.css'],
  },
};

const appConfig = merge(baseConfig, {
  entry: {
    app: getEntrySources('app'),
    vendor: ['axios', 'react', 'react-dom'],
  },
  plugins: [
    new BundleTracker({
      filename: './webpack.manifest.app.json',
    }),
  ],
});

const managerConfig = merge(baseConfig, {
  entry: {
    manager: getEntrySources('manager'),
  },
  plugins: [
    new BundleTracker({
      filename: './webpack.manifest.manager.json',
    }),
  ],
});

module.exports = [appConfig, managerConfig];
module.exports.configs = { appConfig, managerConfig };
