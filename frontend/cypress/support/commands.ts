// C:\Users\Vinay\Project\frontend\cypress\support\commands.ts

/// <reference types="cypress" />

// --- Command Implementations ---

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

Cypress.Commands.add('createTestUser', (username, password) => {
  const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');
  cy.request({
    method: 'POST',
    url: `${apiBaseUrl}/api/test/create-user/`,
    body: {
      username,
      password,
    },
  });
});

// --- NEW COMMAND ADDED FOR FOLLOWING ---
Cypress.Commands.add('createFollow', (follower, following) => {
  const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');
  cy.request({
    method: 'POST',
    url: `${apiBaseUrl}/api/test/create-follow/`,
    body: {
      follower,
      following,
    },
  });
});
// --- END OF NEW COMMAND ---


// --- TypeScript Type Definitions ---
// This block is the "dictionary" that tells TypeScript about all our custom commands.
declare global {
  namespace Cypress {
    interface Chainable {
      login(username?: string, password?: string): Chainable<void>
      createTestUser(username: string, password: string): Chainable<void>
      // --- NEW TYPE DECLARATION ADDED HERE ---
      createFollow(follower: string, following: string): Chainable<void>
    }
  }
}

// This line is required to make the file a module.
export {}