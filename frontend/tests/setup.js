/**
 * Jest setup file
 * Initializes global test utilities and mocks
 */
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  // error and others kept to see output
};
