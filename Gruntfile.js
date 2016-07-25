module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    migrate: {
      options: {
        dir: "migrations",
        env: {
          DATABASE_URL:  process.env.TRANSLATIONS_SERVER_DB_URL
        },
        verbose: true,
        "sql-file": true,
      }
    }
  });

  // Load the plug-ins.
  require('jit-grunt')(grunt, {
    migrate: 'grunt-db-migrate'
  });

  // Tasks.  
  grunt.registerTask('default', ['migrate']);
};
