// C:\Users\Vinay\Project\frontend\cypress\support\commands.ts

/// <reference types="cypress" />

// This is the custom login command that makes a direct API request.
Cypress.Commands.add('login', (username = 'abc1', password = 'Airtel@123') => {
  // cy.session caches the login state (localStorage, cookies) across tests,
  // making subsequent tests run much faster.
  cy.session([username, password], () => {
    // CORRECTED: Read the API base URL from the environment variables we set up.
    // This comes from the CYPRESS_API_BASE_URL in your .env.cy.network file.
    const apiBaseUrl = Cypress.env('CYPRESS_API_BASE_URL');

    cy.request({
      method: 'POST',
      // CORRECTED: Build the URL dynamically. No more hardcoding!
      url: `${apiBaseUrl}/api/auth/login/`,
      body: { username, password },
    }).then(({ body }) => {
      // After a successful API login, set the token in localStorage
      // so the frontend application can pick it up when we cy.visit().
      window.localStorage.setItem('authToken', body.key);
    });
  });
});

// This is the TypeScript declaration that tells VS Code about our new command,
// preventing type errors and enabling autocomplete.
declare global {
  namespace Cypress {
    interface Chainable {
      login(username?: string, password?: string): Chainable<void>
    }
  }
}

// To satisfy TypeScript, we need an empty export.
export {}