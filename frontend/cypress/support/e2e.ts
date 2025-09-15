// C:\Users\Vinay\Project\frontend\cypress\support\e2e.ts

// ***********************************************************
// This example support/e2e.ts is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

/**
 * Global After Hook
 * -----------------
 * This code block runs a single time after ALL tests in the suite have finished.
 * Its purpose is to clean up the database by calling the backend's new
 * endpoint with the 'cleanup' action. This prevents test data from
 * polluting the development environment over time.
 */
after(() => {
  cy.log('--- E2E Test Suite Finished: Cleaning up test data ---');

  cy.request({
    method: 'POST',
    // THIS IS THE CORRECTED URL with /test/
    url: `${Cypress.env('VITE_API_BASE_URL')}/api/test/setup/`, 
    body: {
      action: 'cleanup' // The action we created on the backend
    },
    failOnStatusCode: true 
  }).then((response) => {
    cy.log('Cleanup successful:', response.body);
  });
});