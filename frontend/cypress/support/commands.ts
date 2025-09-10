// C:\Users\Vinay\Project\frontend\cypress\support\commands.ts

/// <reference types="cypress" />

// CORRECTED: The cy.session() wrapper has been removed for reliability.
Cypress.Commands.add('login', (username, password) => {
  const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');
  cy.request({
    method: 'POST',
    url: `${apiBaseUrl}/api/auth/login/`,
    body: { username, password },
  }).then(({ body }) => {
    // This command now directly sets the token for the current test.
    window.localStorage.setItem('authToken', body.key);
  });
});

Cypress.Commands.add('testSetup', (action, data) => {
  const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');
  cy.request({
    method: 'POST',
    url: `${apiBaseUrl}/api/test/setup/`,
    body: { action, data },
  });
});

Cypress.Commands.add('logout', () => {
  window.localStorage.removeItem('authToken');
});


// --- TypeScript Type Definitions ---
// The login signature is updated to make arguments required, as they always are.
declare global {
  namespace Cypress {
    interface Chainable {
      login(username: string, password: string): Chainable<void>
      testSetup(action: string, data?: any): Chainable<Cypress.Response<any>>
      logout(): Chainable<void>
    }
  }
}

export {}