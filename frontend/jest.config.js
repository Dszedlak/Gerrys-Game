module.exports = {
  testEnvironment: 'jsdom',
  moduleFileExtensions: ['js', 'jsx', 'json'],
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
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
