// C:\Users\Vinay\Project\frontend\cypress\support\commands.ts

/// <reference types="cypress" />

Cypress.Commands.add('login', (username = 'abc1', password = 'Airtel@123') => {
  cy.session([username, password], () => {
    const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');
    cy.request({
      method: 'POST',
      url: `${apiBaseUrl}/api/auth/login/`,
      body: { username, password },
    }).then(({ body }) => {
      window.localStorage.setItem('authToken', body.key);
    });
  });
});

/**
 * A powerful command to interact with the backend test setup endpoint.
 * It sends a specific action and data payload to the backend.
 * @example
 * cy.testSetup('create_user', { username: 'test1', password: 'pw' })
 * cy.testSetup('create_post', { username: 'test1', content: 'Hello!' })
 * cy.testSetup('create_follow', { follower: 'test1', following: 'abc1' })
 */
Cypress.Commands.add('testSetup', (action, data) => {
  const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');
  cy.request({
    method: 'POST',
    // This URL points to the new endpoint we just created
    url: `${apiBaseUrl}/api/test/setup/`,
    body: { action, data },
  });
});

// --- TypeScript Type Definitions ---
// This part makes sure TypeScript understands our new command.
declare global {
  namespace Cypress {
    interface Chainable {
      login(username?: string, password?: string): Chainable<void>
      testSetup(action: string, data?: any): Chainable<void>
    }
  }
}

export {}