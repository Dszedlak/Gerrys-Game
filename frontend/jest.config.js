module.exports = {
  testEnvironment: 'jsdom',
  moduleFileExtensions: ['js', 'jsx', 'json', 'vue'],
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
    '^.+\\.vue$': '<rootDir>/tests/vueTransform.js',
  },
  transformIgnorePatterns: ['/node_modules/'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: [
    '**/tests/unit/**/*.spec.(js|jsx)',
  ],
  testEnvironmentOptions: {
    url: 'http://localhost/',
    // Load the Node builds of Vue packages (test-utils' browser build expects a global Vue)
    customExportConditions: ['node', 'node-addons'],
  },
  collectCoverage: false,
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/main.js',
    '!src/router/index.js',
    '!**/node_modules/**',
  ],
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
};
