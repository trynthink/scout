module.exports = function(grunt) {

  // Load all grunt tasks
  require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

  grunt.initConfig({
    // Open the desired local port for previewing content in the browser
    open: {
      dev: {
        path: 'http://localhost:1919'
      }
    },
    // Link built HTML version of documentation to the local open port
    connect: {
      server: {
        options: {
          port: 1919,
          base: './_build/html',
          livereload: true
        }
      }
    },
    // Define commands to execute at the command line
    exec: {
      build_sphinx: {
        cmd: 'make html'
      }
    },
    // Watch for changes in the project directory and run tasks when changes are detected
    watch: {
      // Places to look for modified files to trigger a sphinx re-build
      sphinx: {
        files: ['./**/*.rst', './**/*.py', './examples/*', './images/*'],
        tasks: ['exec:build_sphinx']
      },
      // Automatically reload the HTML documentation if sphinx re-builds
      livereload: {
        files: ['./_build/html/*'],
        options: { livereload: true }
      }
    }
  });

  // Load required plugins
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-contrib-connect');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-open');

  // Define commands triggered when 'grunt' is run at the command line
  grunt.registerTask('default', ['exec', 'connect', 'open', 'watch']);

};