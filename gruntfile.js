module.exports = function(grunt) {
  // Load all grunt tasks
  require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

  grunt.initConfig({
    // Check JSON files located at the paths specified in 'src'
    jsonlint: {
      sample: {
        // Multiple file locations can be specified in this list
        src: ['ecm_definitions/*.json'],
        options: {
          formatter: 'prose'
        }
      }
    }
  });

  // Load required plugins
  grunt.loadNpmTasks('grunt-jsonlint');

  // Define commands to run when the `grunt travis` command is run
  grunt.registerTask('travis', ['jsonlint'])
};