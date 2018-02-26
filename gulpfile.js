const gulp = require("gulp");
const gutil = require("gulp-util");
const webpack = require("webpack");
const webpackStream = require('webpack-stream');
const webpackConfig = require('./webpack.config.js');
const browserSync = require('browser-sync').create();


gulp.task('html', () => {
    gulp.src('./html/**/*.html')
        .pipe(gulp.dest('./dist/'))
});

gulp.task('js', () => {
    gulp.src('./src/**/*.*')
        .pipe(webpackStream(webpackConfig), webpack)
        .pipe(gulp.dest('./dist/'));
});

gulp.task('watch', ['build'], () => {
    browserSync.init({
        server: "./dist/"
    });
    gulp.watch('./html/**/*.html', ['html']);
    gulp.watch('./src/**/*.*', ['js']);

});

gulp.task('images', () => {
    gulp.src('./images/**/*.*')
        .pipe(gulp.dest('./dist/'));
});

gulp.task('build', ['js', 'html', 'images']);
