var webpack = require('webpack');
var path = require('path');


module.exports = {
    devtool: 'source-map',
    entry: [
        path.join(__dirname, 'src/index.jsx')
    ],
    module: {
        loaders: [{
            test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                loader: 'babel-loader'
            },{
                test: /\.less$/,
                loaders: ["style-loader", "css-loder", "less-loader"]
            },
            {
                test: /\.json$/,
                loader: 'json-loader'
            }
        ]
    },
    output: {
        path: __dirname + '/dist',
        filename: 'bundle.js'
    },
    resolve: {
      extensions: ['.js', '.jsx', '.json']
    },
    devServer: {
        contentBase: path.join(__dirname, 'html/'),
        historyApiFallback: true
    }
}
