var gulp = require('gulp');
var util = require('gulp-util');
var plumber = require('gulp-plumber');
var sass = require('gulp-ruby-sass');
var sass = require('gulp-sass');

var sassMain = 'website/static/stylesheets/styles.sass';
var cssDir = 'website/static/stylesheets/';

// Refer to this tutorial: https://css-tricks.com/gulp-for-beginners/
// watches sass files for changes and recompiles on the fly

gulp.task('sass', function(){
  return gulp.src(sassMain).pipe(sass()).pipe(gulp.dest(cssDir))
});

gulp.task('watch', function(){
  gulp.watch('**/*.sass', gulp.series('sass'));
});

// gulp.watch('**/*.sass', ['compileSass']);


// gulp.task('compileSass', function() {
//   return sass(sassMain)
//     .on('error', sass.logError)
//     .pipe(gulp.dest(cssDir));
// });
